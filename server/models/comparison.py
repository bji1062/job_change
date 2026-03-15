from pydantic import BaseModel
from datetime import datetime

class ComparisonReq(BaseModel):
    company_a_name: str | None = None
    type_a: str
    salary_a_min: int | None = None
    salary_a_max: int | None = None
    commute_a: int = 0
    work_style_a: dict | None = None
    benefits_a: list[dict] | None = None
    company_b_name: str | None = None
    type_b: str
    salary_rate: int | None = None
    commute_b: int = 0
    work_style_b: dict | None = None
    benefits_b: list[dict] | None = None
    priority_key: str
    sacrifice_key: str | None = None

class ComparisonResp(ComparisonReq):
    id: int
    created_at: datetime
