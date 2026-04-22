from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.auth_service import decode_token, decode_token_full

bearer = HTTPBearer()

async def get_current_user(cred: HTTPAuthorizationCredentials = Depends(bearer)) -> int:
    mbr_id = decode_token(cred.credentials)
    if mbr_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return mbr_id

async def get_verified_user_for_comp(
    comp_id: int,
    cred: HTTPAuthorizationCredentials = Depends(bearer),
) -> int:
    """해당 comp_id 회사의 이메일로 인증된 사용자만 허용 (admin은 면제).

    JWT cev 클레임은 인증된 회사의 comp_id(int). bool 값은 권한 없음으로 간주.
    """
    payload = decode_token_full(cred.credentials)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    if payload.get("role_cd") == "admin":
        return int(payload["sub"])
    cev = payload.get("cev")
    if isinstance(cev, bool) or not isinstance(cev, int) or cev != comp_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 회사의 이메일 인증이 필요합니다",
        )
    return int(payload["sub"])


_optional_bearer = HTTPBearer(auto_error=False)

async def get_optional_user(
    cred: HTTPAuthorizationCredentials | None = Depends(_optional_bearer),
) -> int | None:
    """익명 허용 엔드포인트용 — 토큰 없으면 None, 유효하지 않아도 None.

    예: 사용자 제보 API — 로그인이면 mbr_id 기록, 비로그인도 허용.
    """
    if cred is None:
        return None
    mbr_id = decode_token(cred.credentials)
    return mbr_id  # 유효하지 않으면 None


async def get_admin_user(cred: HTTPAuthorizationCredentials = Depends(bearer)) -> int:
    payload = decode_token_full(cred.credentials)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    if payload.get("role_cd") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return int(payload["sub"])
