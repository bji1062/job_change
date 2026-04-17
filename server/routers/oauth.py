import secrets
import time
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse

import config
import database
from models.oauth import CompanyEmailReq
from middleware.auth_middleware import get_current_user
from services.auth_service import (
    create_token,
    find_or_create_social_user,
    is_company_email,
    send_verification_email,
)

router = APIRouter()

# ━━ In-memory OAuth state 관리 ━━
_oauth_states: dict[str, float] = {}
STATE_TTL = 300  # 5분

PROVIDERS = {
    "kakao": {
        "auth_url": "https://kauth.kakao.com/oauth/authorize",
        "token_url": "https://kauth.kakao.com/oauth/token",
        "userinfo_url": "https://kapi.kakao.com/v2/user/me",
        "scope": "profile_nickname,account_email",
    },
    "naver": {
        "auth_url": "https://nid.naver.com/oauth2.0/authorize",
        "token_url": "https://nid.naver.com/oauth2.0/token",
        "userinfo_url": "https://openapi.naver.com/v1/nid/me",
        "scope": "",
    },
    "google": {
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
        "scope": "openid email profile",
    },
}


def _get_client_config(provider: str) -> tuple[str, str]:
    """provider별 client_id, client_secret 반환"""
    if provider == "kakao":
        return config.KAKAO_CLIENT_ID, config.KAKAO_CLIENT_SECRET
    elif provider == "naver":
        return config.NAVER_CLIENT_ID, config.NAVER_CLIENT_SECRET
    elif provider == "google":
        return config.GOOGLE_CLIENT_ID, config.GOOGLE_CLIENT_SECRET
    raise ValueError(f"Unknown provider: {provider}")


def _cleanup_expired_states():
    """만료된 state 정리"""
    now = time.time()
    expired = [s for s, t in _oauth_states.items() if now - t > STATE_TTL]
    for s in expired:
        _oauth_states.pop(s, None)


def _parse_userinfo(provider: str, data: dict) -> tuple[str, str | None, str, bool]:
    """provider별 응답에서 (provider_id, email, name, email_verified) 추출"""
    if provider == "kakao":
        pid = str(data["id"])
        account = data.get("kakao_account", {})
        email = account.get("email")
        ev = account.get("is_email_verified", False)
        name = account.get("profile", {}).get("nickname", "")
        return pid, email, name, bool(ev)
    elif provider == "naver":
        resp = data["response"]
        pid = str(resp["id"])
        email = resp.get("email")
        name = resp.get("name", "")
        return pid, email, name, True  # 네이버 이메일은 기본 검증됨
    elif provider == "google":
        pid = str(data["id"])
        email = data.get("email")
        ev = data.get("verified_email", False)
        name = data.get("name", "")
        return pid, email, name, bool(ev)
    raise ValueError(f"Unknown provider: {provider}")


# ━━ OAuth 로그인 ━━

@router.get("/{provider}/login")
async def oauth_login(provider: str):
    if provider not in PROVIDERS:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 provider: {provider}")

    client_id, _ = _get_client_config(provider)
    if not client_id:
        raise HTTPException(status_code=500, detail=f"{provider} OAuth가 설정되지 않았습니다")

    _cleanup_expired_states()
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = time.time()

    prov = PROVIDERS[provider]
    redirect_uri = f"{config.OAUTH_REDIRECT_BASE}/api/v1/oauth/{provider}/callback"

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "state": state,
    }
    if prov["scope"]:
        params["scope"] = prov["scope"]
    if provider == "google":
        params["access_type"] = "offline"

    auth_url = f"{prov['auth_url']}?{urlencode(params)}"
    return RedirectResponse(url=auth_url)


@router.get("/{provider}/callback")
async def oauth_callback(provider: str, code: str = Query(...), state: str = Query(...)):
    if provider not in PROVIDERS:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 provider: {provider}")

    # state 검증
    ts = _oauth_states.pop(state, None)
    if ts is None or time.time() - ts > STATE_TTL:
        raise HTTPException(status_code=400, detail="유효하지 않거나 만료된 state")

    client_id, client_secret = _get_client_config(provider)
    prov = PROVIDERS[provider]
    redirect_uri = f"{config.OAUTH_REDIRECT_BASE}/api/v1/oauth/{provider}/callback"

    # 1. access_token 획득
    token_data = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        token_resp = await client.post(prov["token_url"], data=token_data)
        if token_resp.status_code != 200:
            raise HTTPException(status_code=502, detail="OAuth token 요청 실패")
        token_json = token_resp.json()
        access_token = token_json.get("access_token")
        if not access_token:
            raise HTTPException(status_code=502, detail="access_token을 받지 못했습니다")

        # 2. 유저 정보 조회
        headers = {"Authorization": f"Bearer {access_token}"}
        info_resp = await client.get(prov["userinfo_url"], headers=headers)
        if info_resp.status_code != 200:
            raise HTTPException(status_code=502, detail="사용자 정보 조회 실패")
        userinfo = info_resp.json()

    provider_id, email_addr, mbr_nm, email_verified = _parse_userinfo(provider, userinfo)

    # 3. DB 사용자 조회/생성 (이메일 미검증 시 자동 연동 차단)
    user = await find_or_create_social_user(provider, provider_id, email_addr, mbr_nm, email_verified=email_verified)

    # 4. JWT 발급 후 프론트엔드로 리다이렉트
    verified = user.get("comp_email_vrfc_yn") == 'Y'
    vrfc_comp_id = user.get("vrfc_comp_id")
    cev = int(vrfc_comp_id) if verified and vrfc_comp_id is not None else None
    token = create_token(user["mbr_id"], user["role_cd"], cev=cev)
    redirect_params = urlencode({
        "token": token,
        "mbr_id": user["mbr_id"],
        "mbr_nm": user["mbr_nm"] or "",
        "role_cd": user["role_cd"],
        "cev": 1 if verified else 0,
    })
    return RedirectResponse(url=f"{config.OAUTH_REDIRECT_BASE}/?{redirect_params}")


# ━━ 회사 이메일 인증 ━━

@router.post("/company-email/request")
async def request_company_email(req: CompanyEmailReq, mbr_id: int = Depends(get_current_user)):
    if not is_company_email(req.email_addr):
        raise HTTPException(status_code=400, detail="회사 이메일만 사용 가능합니다")

    comp = await database.fetch_one(
        "SELECT COMP_ID AS comp_id FROM TCOMPANY WHERE COMP_ID=%s", (req.comp_id,)
    )
    if not comp:
        raise HTTPException(status_code=404, detail="존재하지 않는 회사입니다")

    # 이전 미인증 토큰 무효화
    await database.execute(
        "UPDATE TEMAIL_VERIFICATION SET VERIFIED_DTM=NOW() WHERE MBR_ID=%s AND VERIFIED_DTM IS NULL",
        (mbr_id,),
    )
    token = secrets.token_urlsafe(48)
    await database.execute(
        "INSERT INTO TEMAIL_VERIFICATION (MBR_ID, COMP_ID, EMAIL_ADDR, TOKEN_VAL, EXPIRES_DTM) VALUES (%s, %s, %s, %s, DATE_ADD(NOW(), INTERVAL 24 HOUR))",
        (mbr_id, req.comp_id, req.email_addr, token),
    )
    await send_verification_email(req.email_addr, token)
    return {"ok": True, "message": "인증 이메일을 발송했습니다"}


@router.get("/company-email/verify")
async def verify_company_email(token: str = Query(...)):
    row = await database.fetch_one(
        """SELECT VERIFY_ID AS verify_id, MBR_ID AS mbr_id, COMP_ID AS comp_id,
                  EMAIL_ADDR AS email_addr
           FROM TEMAIL_VERIFICATION
           WHERE TOKEN_VAL=%s AND VERIFIED_DTM IS NULL AND EXPIRES_DTM > NOW()""",
        (token,),
    )
    if not row:
        raise HTTPException(status_code=400, detail="유효하지 않거나 만료된 인증 링크")

    await database.execute(
        "UPDATE TEMAIL_VERIFICATION SET VERIFIED_DTM=NOW() WHERE VERIFY_ID=%s",
        (row["verify_id"],),
    )
    await database.execute(
        "UPDATE TMEMBER SET COMP_EMAIL_ADDR=%s, COMP_EMAIL_VRFC_YN='Y', VRFC_COMP_ID=%s WHERE MBR_ID=%s",
        (row["email_addr"], row["comp_id"], row["mbr_id"]),
    )
    return RedirectResponse(url=f"{config.OAUTH_REDIRECT_BASE}/?email_verified=1")


# ━━ 내 정보 조회 ━━

@router.get("/me")
async def get_me(mbr_id: int = Depends(get_current_user)):
    user = await database.fetch_one(
        """SELECT MBR_ID AS mbr_id, EMAIL_ADDR AS email_addr, MBR_NM AS mbr_nm,
                  ROLE_CD AS role_cd, LOGIN_PROVIDER_CD AS login_provider_cd,
                  COMP_EMAIL_ADDR AS comp_email_addr,
                  COMP_EMAIL_VRFC_YN AS comp_email_vrfc_yn
           FROM TMEMBER WHERE MBR_ID=%s""",
        (mbr_id,),
    )
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    return user
