import json
import traceback
from fastapi import APIRouter, Depends
import database
from services import cache
from middleware.auth_middleware import get_current_user
from models.comparison import ComparisonReq

router = APIRouter()

@router.post("")
async def create(req: ComparisonReq, user_id: int = Depends(get_current_user)):
    cid = await database.execute(
        """INSERT INTO comparisons
           (user_id, company_a_name, type_a, salary_a_min, salary_a_max, commute_a,
            work_style_a, benefits_a, company_b_name, type_b, salary_rate, commute_b,
            work_style_b, benefits_b, priority_key, sacrifice_key)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (user_id, req.company_a_name, req.type_a, req.salary_a_min, req.salary_a_max,
         req.commute_a, json.dumps(req.work_style_a) if req.work_style_a else None,
         json.dumps(req.benefits_a) if req.benefits_a else None,
         req.company_b_name, req.type_b, req.salary_rate, req.commute_b,
         json.dumps(req.work_style_b) if req.work_style_b else None,
         json.dumps(req.benefits_b) if req.benefits_b else None,
         req.priority_key, req.sacrifice_key),
    )
    # Feed auto-generation
    if req.feed_headline:
        try:
            await database.execute(
                """INSERT INTO comparison_feed
                   (comparison_id, job_category, company_a_display, type_a,
                    company_b_display, type_b, headline, detail,
                    metric_val, metric_label, metric_type)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (cid, req.feed_job_category, req.company_a_name or '현직', req.type_a,
                 req.company_b_name or '이직처', req.type_b, req.feed_headline,
                 req.feed_detail, req.feed_metric_val, req.feed_metric_label,
                 req.feed_metric_type or 'neu'))
        except Exception:
            pass
    # Auto-upsert into popular_cases
    print(f"[popular_cases] company_a={req.company_a_name!r}, company_b={req.company_b_name!r}")
    if req.company_a_name and req.company_b_name:
        try:
            type_labels = {
                'large': '대기업', 'mid': '중견기업', 'public': '공기업',
                'startup': '스타트업', 'foreign': '외국계', 'freelance': '프리랜서'
            }
            # Check if this pair already exists (A vs B or B vs A)
            existing = await database.fetch_one(
                """SELECT id FROM popular_cases
                   WHERE (title_a=%s AND title_b=%s) OR (title_a=%s AND title_b=%s)
                   LIMIT 1""",
                (req.company_a_name, req.company_b_name,
                 req.company_b_name, req.company_a_name))
            print(f"[popular_cases] existing={existing}")
            if existing:
                await database.execute(
                    "UPDATE popular_cases SET comparison_count=comparison_count+1 WHERE id=%s",
                    (existing["id"],))
                print(f"[popular_cases] UPDATE done for id={existing['id']}")
            else:
                points = json.dumps(req.feed_points[:3], ensure_ascii=False) if req.feed_points else '[]'
                await database.execute(
                    """INSERT INTO popular_cases
                       (case_type, title_a, type_a, sub_a, title_b, type_b, sub_b,
                        points, view_count, comparison_count)
                       VALUES ('company',%s,%s,%s,%s,%s,%s,%s,0,1)""",
                    (req.company_a_name, req.type_a, type_labels.get(req.type_a, req.type_a),
                     req.company_b_name, req.type_b, type_labels.get(req.type_b, req.type_b),
                     points))
                print(f"[popular_cases] INSERT done: {req.company_a_name} vs {req.company_b_name}")
            cache.delete("landing_popular")
        except Exception as e:
            print(f"[popular_cases upsert error] {e}")
            traceback.print_exc()
    else:
        print(f"[popular_cases] SKIPPED — company name is None")
    # Daily stats increment
    try:
        await database.execute(
            """INSERT INTO daily_stats (stat_date, comparison_count) VALUES (CURDATE(), 1)
               ON DUPLICATE KEY UPDATE comparison_count = comparison_count + 1""")
    except Exception:
        pass
    # Invalidate feed cache
    cache.set("landing_feed", None, ttl=0)
    return {"id": cid}

@router.get("")
async def list_mine(user_id: int = Depends(get_current_user)):
    rows = await database.fetch_all(
        """SELECT id, company_a_name, type_a, company_b_name, type_b,
                  priority_key, created_at
           FROM comparisons WHERE user_id=%s ORDER BY created_at DESC LIMIT 50""",
        (user_id,),
    )
    for r in rows:
        if r.get("created_at"):
            r["created_at"] = r["created_at"].isoformat()
    return rows

@router.get("/{comparison_id}")
async def get_one(comparison_id: int, user_id: int = Depends(get_current_user)):
    row = await database.fetch_one(
        "SELECT * FROM comparisons WHERE id=%s AND user_id=%s", (comparison_id, user_id)
    )
    if not row:
        return {"error": "not found"}
    for k in ("work_style_a", "work_style_b", "benefits_a", "benefits_b"):
        if isinstance(row.get(k), str):
            row[k] = json.loads(row[k])
    if row.get("created_at"):
        row["created_at"] = row["created_at"].isoformat()
    return row
