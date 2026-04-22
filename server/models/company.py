from pydantic import BaseModel, Field

from models.types import (
    BadgeCd, BadgeSrcCd, BenefitCtgrCd, BenefitReportTypeCd, CompTpCd,
)


class CompanyBrief(BaseModel):
    comp_id: int
    comp_nm: str
    comp_tp_cd: CompTpCd
    industry_nm: str | None = None
    logo_nm: str | None = None

class Benefit(BaseModel):
    benefit_cd: str
    benefit_nm: str
    benefit_amt: int = 0
    benefit_ctgr_cd: BenefitCtgrCd
    badge_cd: BadgeCd = "est"
    badge_src_cd: BadgeSrcCd | None = None
    badge_src_url_ctnt: str | None = None
    note_ctnt: str | None = None
    qual_yn: bool = False
    qual_desc_ctnt: str | None = None

class BenefitUpsert(BaseModel):
    benefit_cd: str
    benefit_nm: str
    benefit_amt: int = 0
    benefit_ctgr_cd: BenefitCtgrCd
    badge_cd: BadgeCd = "est"
    badge_src_cd: BadgeSrcCd | None = None
    badge_src_url_ctnt: str | None = None
    note_ctnt: str | None = None
    qual_yn: bool = False
    qual_desc_ctnt: str | None = None
    sort_order_no: int = 0

class CompanyDetail(CompanyBrief):
    benefits: list[Benefit] = []
    work_style_val: dict | None = None
    aliases: list[str] = []

class BenefitReportReq(BaseModel):
    report_type_cd: BenefitReportTypeCd
    reported_amt: int | None = None  # wrong_amount 일 때 제보자가 주장하는 값 (만원)
    comment_ctnt: str | None = Field(default=None, max_length=500)
