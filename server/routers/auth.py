from fastapi import APIRouter, HTTPException, status
import database
from models.user import RegisterReq, LoginReq, TokenResp
from services.auth_service import hash_password, verify_password, create_token

router = APIRouter()

@router.post("/register", response_model=TokenResp)
async def register(req: RegisterReq):
    existing = await database.fetch_one("SELECT MBR_ID AS id FROM TMEMBER WHERE EMAIL_ADDR=%s", (req.email,))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    pw_hash = hash_password(req.password)
    user_id = await database.execute(
        "INSERT INTO TMEMBER (EMAIL_ADDR, PWD_HASH_VAL, MBR_NM, JOB_NM) VALUES (%s, %s, %s, %s)",
        (req.email, pw_hash, req.name, req.job_nm),
    )
    token = create_token(user_id)
    return TokenResp(access_token=token, user_id=user_id, name=req.name, role="user")

@router.post("/login", response_model=TokenResp)
async def login(req: LoginReq):
    user = await database.fetch_one(
        "SELECT MBR_ID AS id, PWD_HASH_VAL AS password_hash, MBR_NM AS name, ROLE_CD AS role, COMP_EMAIL_VRFC_YN AS company_email_verification_yn FROM TMEMBER WHERE EMAIL_ADDR=%s",
        (req.email,),
    )
    if not user or not user["password_hash"] or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    role = user.get("role") or "user"
    cev = user.get("company_email_verification_yn") == 'Y'
    token = create_token(user["id"], role, cev=cev)
    return TokenResp(
        access_token=token, user_id=user["id"], name=user["name"],
        role=role, company_email_verified=cev,
    )
