from pydantic import BaseModel

class CompanyBrief(BaseModel):
    id: str
    name: str
    type: str
    industry: str | None = None
    logo: str | None = None

class Benefit(BaseModel):
    key: str
    name: str
    val: int = 0
    cat: str
    badge: str = "est"
    note: str | None = None
    qual: bool = False
    qualText: str | None = None

class BenefitUpsert(BaseModel):
    key: str
    name: str
    val: int = 0
    cat: str
    badge: str = "est"
    note: str | None = None
    qual: bool = False
    qualText: str | None = None
    sortOrder: int = 0

class CompanyDetail(CompanyBrief):
    benefits: list[Benefit] = []
    workStyle: dict | None = None
    aliases: list[str] = []
