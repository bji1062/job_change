from pydantic import BaseModel, EmailStr


class CompanyEmailReq(BaseModel):
    email: EmailStr
