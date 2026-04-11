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
        """SELECT FEED_ID AS id, JOB_CTGR_NM AS job_category,
                  COMP_A_DISP_NM AS company_a_display, COMP_A_TP_CD AS type_a,
                  COMP_B_DISP_NM AS company_b_display, COMP_B_TP_CD AS type_b,
                  HEADLINE_CTNT AS headline, DETAIL_CTNT AS detail,
                  METRIC_VAL_CTNT AS metric_val, METRIC_LABEL_NM AS metric_label,
                  METRIC_TYPE_CD AS metric_type, INS_DTM AS created_at
           FROM TCOMPARISON_FEED
           WHERE INS_DTM >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
           ORDER BY INS_DTM DESC LIMIT 10"""
    )
    for r in rows:
        if r.get("created_at"):
            from datetime import timezone
            r["created_at"] = r["created_at"].replace(tzinfo=timezone.utc).isoformat()
    cache.set("landing_feed", rows, ttl=300)
    return rows

@router.get("/stats")
async def get_stats():
    row = await database.fetch_one(
        "SELECT COMPARISON_NO AS comparison_count FROM TDAILY_STAT WHERE STAT_DT = CURDATE()"
    )
    total_row = await database.fetch_one(
        "SELECT COUNT(*) AS cnt FROM TCOMPARISON"
    )
    today = int(row["comparison_count"]) if row else 0
    total = int(total_row["cnt"]) if total_row else 0
    return {"today_comparisons": today, "total_comparisons": total, "active_visitors": _get_active_count()}

@router.get("/popular")
async def get_popular():
    cached = cache.get("landing_popular")
    if cached is not None:
        return cached
    rows = await database.fetch_all(
        """SELECT CASE_ID AS id, CASE_TYPE_CD AS case_type,
                  TITLE_A_NM AS title_a, TYPE_A_CD AS type_a, SUB_A_NM AS sub_a,
                  TITLE_B_NM AS title_b, TYPE_B_CD AS type_b, SUB_B_NM AS sub_b,
                  POINTS_VAL AS points,
                  VIEW_NO AS view_count, COMPARISON_NO AS comparison_count
           FROM TPOPULAR_CASE WHERE ACTIVE_YN=1
           ORDER BY COMPARISON_NO DESC, VIEW_NO DESC LIMIT 10"""
    )
    for r in rows:
        if isinstance(r.get("points"), str):
            r["points"] = json.loads(r["points"])
    cache.set("landing_popular", rows, ttl=3600)
    return rows

@router.post("/popular/{case_id}/view")
async def increment_view(case_id: int):
    await database.execute(
        "UPDATE TPOPULAR_CASE SET VIEW_NO = VIEW_NO + 1 WHERE CASE_ID = %s",
        (case_id,)
    )
    row = await database.fetch_one(
        "SELECT VIEW_NO AS view_count FROM TPOPULAR_CASE WHERE CASE_ID = %s", (case_id,)
    )
    # Invalidate cache so next load reflects updated count
    cache.delete("landing_popular")
    return {"view_count": int(row["view_count"]) if row else 0}

@router.post("/ping")
async def ping(req: PingReq):
    _active_visitors[req.client_id] = time.time()
    total_row = await database.fetch_one(
        "SELECT COUNT(*) AS cnt FROM TCOMPARISON"
    )
    total = int(total_row["cnt"]) if total_row else 0
    return {"active_visitors": _get_active_count(), "total_comparisons": total}
