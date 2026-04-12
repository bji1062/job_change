from pydantic import BaseModel, EmailStr


class CompanyEmailReq(BaseModel):
    email_addr: EmailStr
