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
            from datetime import timezone
            r["created_at"] = r["created_at"].replace(tzinfo=timezone.utc).isoformat()
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

@router.get("/popular/debug")
async def debug_popular():
    """Diagnostic endpoint — check popular_cases table status"""
    result = {}
    # 1. Count rows
    try:
        row = await database.fetch_one("SELECT COUNT(*) AS cnt FROM popular_cases")
        result["total_rows"] = int(row["cnt"]) if row else 0
    except Exception as e:
        result["total_rows_error"] = str(e)
    # 2. Show all rows (basic info)
    try:
        rows = await database.fetch_all(
            "SELECT id, title_a, title_b, view_count, comparison_count, is_active FROM popular_cases ORDER BY id DESC LIMIT 20"
        )
        result["rows"] = rows
    except Exception as e:
        result["rows_error"] = str(e)
    # 3. Test INSERT + DELETE
    try:
        test_points = json.dumps(["test"], ensure_ascii=False)
        tid = await database.execute(
            """INSERT INTO popular_cases
               (case_type, title_a, type_a, sub_a, title_b, type_b, sub_b,
                points, view_count, comparison_count)
               VALUES ('company',%s,%s,%s,%s,%s,%s,%s,0,1)""",
            ("__TEST_A__", "large", "테스트", "__TEST_B__", "startup", "테스트", test_points))
        result["test_insert"] = {"success": True, "id": tid}
        await database.execute("DELETE FROM popular_cases WHERE id=%s", (tid,))
        result["test_cleanup"] = True
    except Exception as e:
        result["test_insert_error"] = str(e)
    # 4. Cache status
    cached = cache.get("landing_popular")
    result["cache_status"] = "hit" if cached is not None else "miss"
    result["cache_data_len"] = len(cached) if cached else 0
    return result

@router.post("/ping")
async def ping(req: PingReq):
    _active_visitors[req.client_id] = time.time()
    return {"active_visitors": _get_active_count()}
