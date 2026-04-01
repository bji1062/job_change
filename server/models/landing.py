from pydantic import BaseModel
from datetime import datetime

class FeedItem(BaseModel):
    id: int
    job_category: str | None = None
    company_a_display: str
    type_a: str
    company_b_display: str
    type_b: str
    headline: str
    detail: str | None = None
    metric_val: str | None = None
    metric_label: str | None = None
    metric_type: str = "neu"
    created_at: datetime

class PingReq(BaseModel):
    client_id: str

class LandingStats(BaseModel):
    today_comparisons: int = 0
    total_comparisons: int = 0
    active_visitors: int = 0

class PopularCase(BaseModel):
    id: int
    case_type: str
    title_a: str
    type_a: str
    sub_a: str | None = None
    title_b: str
    type_b: str
    sub_b: str | None = None
    points: list[str] | None = None
    view_count: int = 0
    comparison_count: int = 0
