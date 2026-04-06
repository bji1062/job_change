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


def _parse_userinfo(provider: str, data: dict) -> tuple[str, str | None, str]:
    """provider별 응답에서 (provider_id, email, name) 추출"""
    if provider == "kakao":
        pid = str(data["id"])
        account = data.get("kakao_account", {})
        email = account.get("email")
        name = account.get("profile", {}).get("nickname", "")
        return pid, email, name
    elif provider == "naver":
        resp = data["response"]
        pid = str(resp["id"])
        email = resp.get("email")
        name = resp.get("name", "")
        return pid, email, name
    elif provider == "google":
        pid = str(data["id"])
        email = data.get("email")
        name = data.get("name", "")
        return pid, email, name
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

    provider_id, email, name = _parse_userinfo(provider, userinfo)

    # 3. DB 사용자 조회/생성
    user = await find_or_create_social_user(provider, provider_id, email, name)

    # 4. JWT 발급 후 프론트엔드로 리다이렉트
    cev = 1 if user["company_email_verified"] else 0
    token = create_token(user["id"], user["role"], cev=bool(cev))
    redirect_params = urlencode({
        "token": token,
        "uid": user["id"],
        "name": user["name"] or "",
        "role": user["role"],
        "cev": cev,
    })
    return RedirectResponse(url=f"{config.OAUTH_REDIRECT_BASE}/?{redirect_params}")


# ━━ 회사 이메일 인증 ━━

@router.post("/company-email/request")
async def request_company_email(req: CompanyEmailReq, user_id: int = Depends(get_current_user)):
    if not is_company_email(req.email):
        raise HTTPException(status_code=400, detail="회사 이메일만 사용 가능합니다")

    token = secrets.token_urlsafe(48)
    await database.execute(
        "INSERT INTO email_verifications (user_id, email, token, expires_at) VALUES (%s, %s, %s, DATE_ADD(NOW(), INTERVAL 24 HOUR))",
        (user_id, req.email, token),
    )
    await send_verification_email(req.email, token)
    return {"ok": True, "message": "인증 이메일을 발송했습니다"}


@router.get("/company-email/verify")
async def verify_company_email(token: str = Query(...)):
    row = await database.fetch_one(
        "SELECT id, user_id, email FROM email_verifications WHERE token=%s AND verified_at IS NULL AND expires_at > NOW()",
        (token,),
    )
    if not row:
        raise HTTPException(status_code=400, detail="유효하지 않거나 만료된 인증 링크")

    await database.execute(
        "UPDATE email_verifications SET verified_at=NOW() WHERE id=%s",
        (row["id"],),
    )
    await database.execute(
        "UPDATE users SET company_email=%s, company_email_verified=1 WHERE id=%s",
        (row["email"], row["user_id"]),
    )
    return RedirectResponse(url=f"{config.OAUTH_REDIRECT_BASE}/?email_verified=1")


# ━━ 내 정보 조회 ━━

@router.get("/me")
async def get_me(user_id: int = Depends(get_current_user)):
    user = await database.fetch_one(
        "SELECT id, email, name, role, auth_provider, company_email, company_email_verified FROM users WHERE id=%s",
        (user_id,),
    )
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    return user
