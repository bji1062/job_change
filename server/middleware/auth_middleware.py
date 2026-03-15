from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.auth_service import decode_token

bearer = HTTPBearer()

async def get_current_user(cred: HTTPAuthorizationCredentials = Depends(bearer)) -> int:
    user_id = decode_token(cred.credentials)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return user_id
