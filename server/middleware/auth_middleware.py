from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.auth_service import decode_token, decode_token_full

bearer = HTTPBearer()

async def get_current_user(cred: HTTPAuthorizationCredentials = Depends(bearer)) -> int:
    mbr_id = decode_token(cred.credentials)
    if mbr_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return mbr_id

async def get_verified_user(cred: HTTPAuthorizationCredentials = Depends(bearer)) -> int:
    """회사 이메일 인증이 완료된 사용자만 허용 (admin은 면제)"""
    payload = decode_token_full(cred.credentials)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    if payload.get("role_cd") != "admin" and not payload.get("cev"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="회사 이메일 인증이 필요합니다")
    return int(payload["sub"])


async def get_admin_user(cred: HTTPAuthorizationCredentials = Depends(bearer)) -> int:
    payload = decode_token_full(cred.credentials)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    if payload.get("role_cd") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return int(payload["sub"])
