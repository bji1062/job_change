from pydantic import BaseModel
from typing import Any, Literal

from models.types import (
    BadgeCd, BadgeSrcCd, BenefitCtgrCd, CaseTypeCd, CompTpCd, RoleCd,
)


class DashboardStats(BaseModel):
    total_mbr_no: int
    today_mbr_no: int
    total_comparison_no: int
    today_comparison_no: int
    total_comp_no: int
    comp_with_benefit_no: int
    active_visitor_no: int

class CompanyListItem(BaseModel):
    comp_id: int
    comp_nm: str
    comp_tp_cd: str
    industry_nm: str | None = None
    benefit_no: int = 0
    alias_no: int = 0

class CompanyCreate(BaseModel):
    comp_nm: str
    comp_tp_cd: str
    industry_nm: str | None = None
    logo_nm: str | None = None
    work_style_val: dict | None = None
    careers_benefit_url: str | None = None

class CompanyUpdate(BaseModel):
    comp_nm: str | None = None
    comp_tp_cd: str | None = None
    industry_nm: str | None = None
    logo_nm: str | None = None
    work_style_val: dict | None = None
    careers_benefit_url: str | None = None

class AliasUpdate(BaseModel):
    aliases: list[str]

class BenefitItem(BaseModel):
    benefit_cd: str
    benefit_nm: str
    benefit_amt: int = 0
    benefit_ctgr_cd: BenefitCtgrCd = "perks"
    badge_cd: BadgeCd = "est"
    badge_src_cd: BadgeSrcCd | None = None
    badge_src_url_ctnt: str | None = None
    note_ctnt: str | None = None
    qual_yn: bool = False
    qual_desc_ctnt: str | None = None
    sort_order_no: int = 0

class PopularCaseReq(BaseModel):
    case_type_cd: CaseTypeCd
    current_comp_nm: str
    current_comp_tp_cd: CompTpCd
    current_sub_nm: str | None = None
    offer_comp_nm: str
    offer_comp_tp_cd: CompTpCd
    offer_sub_nm: str | None = None
    points_val: list[str] | None = None
    active_yn: bool = True

class UserRoleUpdate(BaseModel):
    role_cd: RoleCd

class BenefitPromoteReq(BaseModel):
    note_ctnt: str | None = None

class BenefitReportResolveReq(BaseModel):
    # 'resolved' 또는 'rejected' 만 허용 — 'open' 으로 되돌리는 워크플로는 없음.
    status_cd: Literal["resolved", "rejected"]
    note_ctnt: str | None = None

class PagedResponse(BaseModel):
    items: list[Any]
    total: int
    page: int
    page_size: int
