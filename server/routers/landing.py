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
        """SELECT id, job_category, company_a_display, type_a,
                  company_b_display, type_b, headline, detail,
                  metric_val, metric_label, metric_type, created_at
           FROM comparison_feed
           WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
           ORDER BY created_at DESC LIMIT 10"""
    )
    for r in rows:
        if r.get("created_at"):
            r["created_at"] = r["created_at"].isoformat()
    cache.set("landing_feed", rows, ttl=300)
    return rows

@router.get("/stats")
async def get_stats():
    row = await database.fetch_one(
        "SELECT comparison_count FROM daily_stats WHERE stat_date = CURDATE()"
    )
    today = int(row["comparison_count"]) if row else 0
    return {"today_comparisons": today, "active_visitors": _get_active_count()}

@router.get("/popular")
async def get_popular():
    cached = cache.get("landing_popular")
    if cached is not None:
        return cached
    rows = await database.fetch_all(
        """SELECT id, case_type, title_a, type_a, sub_a,
                  title_b, type_b, sub_b, points,
                  view_count, comparison_count
           FROM popular_cases WHERE is_active=1
           ORDER BY view_count DESC LIMIT 10"""
    )
    for r in rows:
        if isinstance(r.get("points"), str):
            r["points"] = json.loads(r["points"])
    cache.set("landing_popular", rows, ttl=3600)
    return rows

@router.post("/popular/{case_id}/view")
async def increment_view(case_id: int):
    await database.execute(
        "UPDATE popular_cases SET view_count = view_count + 1 WHERE id = %s",
        (case_id,)
    )
    row = await database.fetch_one(
        "SELECT view_count FROM popular_cases WHERE id = %s", (case_id,)
    )
    # Invalidate cache so next load reflects updated count
    cache.delete("landing_popular")
    return {"view_count": int(row["view_count"]) if row else 0}

@router.post("/ping")
async def ping(req: PingReq):
    _active_visitors[req.client_id] = time.time()
    return {"active_visitors": _get_active_count()}
