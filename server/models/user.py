from pydantic import BaseModel, EmailStr

class RegisterReq(BaseModel):
    email_addr: EmailStr
    password: str
    mbr_nm: str | None = None
    job_nm: str

class LoginReq(BaseModel):
    email_addr: EmailStr
    password: str

class TokenResp(BaseModel):
    access_token: str
    token_type: str = "bearer"
    mbr_id: int
    mbr_nm: str | None = None
    role_cd: str = "user"
    comp_email_vrfc_yn: bool = False
