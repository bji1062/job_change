from fastapi import APIRouter, HTTPException, status
import database
from models.user import RegisterReq, LoginReq, TokenResp
from services.auth_service import hash_password, verify_password, create_token

router = APIRouter()

@router.post("/register", response_model=TokenResp)
async def register(req: RegisterReq):
    existing = await database.fetch_one(
        "SELECT MBR_ID AS mbr_id FROM TMEMBER WHERE EMAIL_ADDR=%s",
        (req.email_addr,),
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    pw_hash = hash_password(req.password)
    mbr_id = await database.execute(
        "INSERT INTO TMEMBER (EMAIL_ADDR, PWD_HASH_VAL, MBR_NM, JOB_NM) VALUES (%s, %s, %s, %s)",
        (req.email_addr, pw_hash, req.mbr_nm, req.job_nm),
    )
    token = create_token(mbr_id)
    return TokenResp(access_token=token, mbr_id=mbr_id, mbr_nm=req.mbr_nm, role_cd="user")

@router.post("/login", response_model=TokenResp)
async def login(req: LoginReq):
    user = await database.fetch_one(
        """SELECT MBR_ID AS mbr_id, PWD_HASH_VAL AS pwd_hash_val, MBR_NM AS mbr_nm,
                  ROLE_CD AS role_cd, COMP_EMAIL_VRFC_YN AS comp_email_vrfc_yn
           FROM TMEMBER WHERE EMAIL_ADDR=%s""",
        (req.email_addr,),
    )
    if not user or not user["pwd_hash_val"] or not verify_password(req.password, user["pwd_hash_val"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    role_cd = user.get("role_cd") or "user"
    cev = user.get("comp_email_vrfc_yn") == 'Y'
    token = create_token(user["mbr_id"], role_cd, cev=cev)
    return TokenResp(
        access_token=token, mbr_id=user["mbr_id"], mbr_nm=user["mbr_nm"],
        role_cd=role_cd, comp_email_vrfc_yn=cev,
    )
