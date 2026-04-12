from pydantic import BaseModel
from datetime import datetime

class FeedItem(BaseModel):
    feed_id: int
    job_ctgr_nm: str | None = None
    comp_a_disp_nm: str
    comp_a_tp_cd: str
    comp_b_disp_nm: str
    comp_b_tp_cd: str
    headline_ctnt: str
    detail_ctnt: str | None = None
    metric_val_ctnt: str | None = None
    metric_label_nm: str | None = None
    metric_type_cd: str = "neu"
    ins_dtm: datetime

class PingReq(BaseModel):
    client_id: str

class LandingStats(BaseModel):
    today_comparison_no: int = 0
    total_comparison_no: int = 0
    active_visitor_no: int = 0

class PopularCase(BaseModel):
    case_id: int
    case_type_cd: str
    title_a_nm: str
    type_a_cd: str
    sub_a_nm: str | None = None
    title_b_nm: str
    type_b_cd: str
    sub_b_nm: str | None = None
    points_val: list[str] | None = None
    view_no: int = 0
    comparison_no: int = 0
