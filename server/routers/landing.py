import time
import json
from fastapi import APIRouter
import database
from services import cache
from models.landing import PingReq

router = APIRouter()

# In-memory visitor tracking
_active_visitors = {}  # {client_id: last_ping_timestamp}
VISITOR_TTL = 60

def _clean_visitors():
    now = time.time()
    expired = [k for k, v in _active_visitors.items() if now - v > VISITOR_TTL]
    for k in expired:
        del _active_visitors[k]

def _get_active_count():
    _clean_visitors()
    return len(_active_visitors)

@router.get("/feed")
async def get_feed():
    cached = cache.get("landing_feed")
    if cached is not None:
        return cached
    rows = await database.fetch_all(
        """SELECT FEED_ID AS feed_id, JOB_CTGR_NM AS job_ctgr_nm,
                  COMP_A_DISP_NM AS comp_a_disp_nm, COMP_A_TP_CD AS comp_a_tp_cd,
                  COMP_B_DISP_NM AS comp_b_disp_nm, COMP_B_TP_CD AS comp_b_tp_cd,
                  HEADLINE_CTNT AS headline_ctnt, DETAIL_CTNT AS detail_ctnt,
                  METRIC_VAL_CTNT AS metric_val_ctnt, METRIC_LABEL_NM AS metric_label_nm,
                  METRIC_TYPE_CD AS metric_type_cd, INS_DTM AS ins_dtm
           FROM TCOMPARISON_FEED
           WHERE INS_DTM >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
           ORDER BY INS_DTM DESC LIMIT 10"""
    )
    for r in rows:
        if r.get("ins_dtm"):
            from datetime import timezone
            r["ins_dtm"] = r["ins_dtm"].replace(tzinfo=timezone.utc).isoformat()
    cache.set("landing_feed", rows, ttl=300)
    return rows

@router.get("/stats")
async def get_stats():
    row = await database.fetch_one(
        "SELECT COMPARISON_NO AS comparison_no FROM TDAILY_STAT WHERE STAT_DT = CURDATE()"
    )
    total_row = await database.fetch_one(
        "SELECT COUNT(*) AS cnt FROM TCOMPARISON"
    )
    today = int(row["comparison_no"]) if row else 0
    total = int(total_row["cnt"]) if total_row else 0
    return {"today_comparison_no": today, "total_comparison_no": total, "active_visitor_no": _get_active_count()}

@router.get("/popular")
async def get_popular():
    cached = cache.get("landing_popular")
    if cached is not None:
        return cached
    rows = await database.fetch_all(
        """SELECT CASE_ID AS case_id, CASE_TYPE_CD AS case_type_cd,
                  TITLE_A_NM AS title_a_nm, TYPE_A_CD AS type_a_cd, SUB_A_NM AS sub_a_nm,
                  TITLE_B_NM AS title_b_nm, TYPE_B_CD AS type_b_cd, SUB_B_NM AS sub_b_nm,
                  POINTS_VAL AS points_val,
                  VIEW_NO AS view_no, COMPARISON_NO AS comparison_no
           FROM TPOPULAR_CASE WHERE ACTIVE_YN=1
           ORDER BY COMPARISON_NO DESC, VIEW_NO DESC LIMIT 10"""
    )
    for r in rows:
        if isinstance(r.get("points_val"), str):
            r["points_val"] = json.loads(r["points_val"])
    cache.set("landing_popular", rows, ttl=3600)
    return rows

@router.post("/popular/{case_id}/view")
async def increment_view(case_id: int):
    await database.execute(
        "UPDATE TPOPULAR_CASE SET VIEW_NO = VIEW_NO + 1 WHERE CASE_ID = %s",
        (case_id,)
    )
    row = await database.fetch_one(
        "SELECT VIEW_NO AS view_no FROM TPOPULAR_CASE WHERE CASE_ID = %s", (case_id,)
    )
    cache.delete("landing_popular")
    return {"view_no": int(row["view_no"]) if row else 0}

@router.post("/ping")
async def ping(req: PingReq):
    _active_visitors[req.client_id] = time.time()
    total_row = await database.fetch_one(
        "SELECT COUNT(*) AS cnt FROM TCOMPARISON"
    )
    total = int(total_row["cnt"]) if total_row else 0
    return {"active_visitor_no": _get_active_count(), "total_comparison_no": total}
