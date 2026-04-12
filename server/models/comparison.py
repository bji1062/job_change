from pydantic import BaseModel
from datetime import datetime

class ComparisonReq(BaseModel):
    comp_a_nm: str | None = None
    comp_a_tp_cd: str
    salary_a_min_amt: int | None = None
    salary_a_max_amt: int | None = None
    commute_a_min_no: int = 0
    work_style_a_val: dict | None = None
    benefits_a_val: list[dict] | None = None
    comp_b_nm: str | None = None
    comp_b_tp_cd: str
    salary_rate_val: int | None = None
    commute_b_min_no: int = 0
    work_style_b_val: dict | None = None
    benefits_b_val: list[dict] | None = None
    priority_cd: str
    sacrifice_cd: str | None = None
    # Feed fields (optional, for landing page social feed)
    feed_headline_ctnt: str | None = None
    feed_detail_ctnt: str | None = None
    feed_metric_val_ctnt: str | None = None
    feed_metric_label_nm: str | None = None
    feed_metric_type_cd: str | None = None
    feed_job_ctgr_nm: str | None = None
    feed_points_val: list[str] | None = None

class ComparisonResp(ComparisonReq):
    comparison_id: int
    ins_dtm: datetime
