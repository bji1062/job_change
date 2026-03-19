from fastapi import APIRouter, HTTPException, status
import database
from models.user import RegisterReq, LoginReq, TokenResp
from services.auth_service import hash_password, verify_password, create_token

router = APIRouter()

@router.post("/register", response_model=TokenResp)
async def register(req: RegisterReq):
    existing = await database.fetch_one("SELECT id FROM users WHERE email=%s", (req.email,))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    pw_hash = hash_password(req.password)
    user_id = await database.execute(
        "INSERT INTO users (email, password_hash, name, job_id) VALUES (%s, %s, %s, %s)",
        (req.email, pw_hash, req.name, req.job_id),
    )
    token = create_token(user_id)
    return TokenResp(access_token=token, user_id=user_id, name=req.name)

@router.post("/login", response_model=TokenResp)
async def login(req: LoginReq):
    user = await database.fetch_one("SELECT id, password_hash, name FROM users WHERE email=%s", (req.email,))
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_token(user["id"])
    return TokenResp(access_token=token, user_id=user["id"], name=user["name"])
