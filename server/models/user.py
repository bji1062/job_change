from pydantic import BaseModel, EmailStr

class RegisterReq(BaseModel):
    email: EmailStr
    password: str
    name: str | None = None

class LoginReq(BaseModel):
    email: EmailStr
    password: str

class TokenResp(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    name: str | None = None
