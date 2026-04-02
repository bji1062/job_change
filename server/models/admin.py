from pydantic import BaseModel
from typing import Any, Literal

class DashboardStats(BaseModel):
    total_users: int
    today_users: int
    total_comparisons: int
    today_comparisons: int
    total_companies: int
    companies_with_benefits: int
    active_visitors: int

class CompanyListItem(BaseModel):
    id: str
    name: str
    type: str
    industry: str | None = None
    benefit_count: int = 0
    alias_count: int = 0

class CompanyCreate(BaseModel):
    name: str
    type_id: str
    industry: str | None = None
    logo: str | None = None
    work_style: dict | None = None
    careers_benefit_url: str | None = None

class CompanyUpdate(BaseModel):
    name: str | None = None
    type_id: str | None = None
    industry: str | None = None
    logo: str | None = None
    work_style: dict | None = None
    careers_benefit_url: str | None = None

class AliasUpdate(BaseModel):
    aliases: list[str]

class BenefitItem(BaseModel):
    ben_key: str
    name: str
    val: int = 0
    category: str = "financial"
    badge: str = "est"
    note: str | None = None
    is_qualitative: bool = False
    qual_text: str | None = None
    sort_order: int = 0

class PopularCaseReq(BaseModel):
    case_type: str
    title_a: str
    type_a: str
    sub_a: str | None = None
    title_b: str
    type_b: str
    sub_b: str | None = None
    points: list[str] | None = None
    is_active: bool = True

class UserRoleUpdate(BaseModel):
    role: Literal["user", "admin"]

class PagedResponse(BaseModel):
    items: list[Any]
    total: int
    page: int
    page_size: int
