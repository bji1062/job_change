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
    try:
        cid = await database.execute(
            """INSERT INTO TCOMPARISON
               (MBR_ID, COMP_A_NM, COMP_A_TP_CD, SALARY_A_MIN_AMT, SALARY_A_MAX_AMT, COMMUTE_A_MIN_NO,
                WORK_STYLE_A_VAL, BENEFITS_A_VAL, COMP_B_NM, COMP_B_TP_CD, SALARY_RATE_VAL, COMMUTE_B_MIN_NO,
                WORK_STYLE_B_VAL, BENEFITS_B_VAL, PRIORITY_CD, SACRIFICE_CD)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (user_id, req.company_a_name, req.type_a, req.salary_a_min, req.salary_a_max,
             req.commute_a, json.dumps(req.work_style_a, ensure_ascii=False) if req.work_style_a else None,
             json.dumps(req.benefits_a, ensure_ascii=False) if req.benefits_a else None,
             req.company_b_name, req.type_b, req.salary_rate, req.commute_b,
             json.dumps(req.work_style_b, ensure_ascii=False) if req.work_style_b else None,
             json.dumps(req.benefits_b, ensure_ascii=False) if req.benefits_b else None,
             req.priority_key, req.sacrifice_key),
        )
    except Exception as e:
        print(f"[comparisons INSERT error] {e}")
        traceback.print_exc()
        return {"error": "comparison save failed"}
    if not cid:
        print(f"[comparisons] WARNING: cid is {cid!r}")
        return {"error": "comparison save failed"}
    # Feed auto-generation
    if req.feed_headline:
        try:
            await database.execute(
                """INSERT INTO TCOMPARISON_FEED
                   (COMPARISON_ID, JOB_CTGR_NM, COMP_A_DISP_NM, COMP_A_TP_CD,
                    COMP_B_DISP_NM, COMP_B_TP_CD, HEADLINE_CTNT, DETAIL_CTNT,
                    METRIC_VAL_CTNT, METRIC_LABEL_NM, METRIC_TYPE_CD)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (cid, req.feed_job_category, req.company_a_name or '현직', req.type_a,
                 req.company_b_name or '이직처', req.type_b, req.feed_headline,
                 req.feed_detail, req.feed_metric_val, req.feed_metric_label,
                 req.feed_metric_type or 'neu'))
            print(f"[comparison_feed] INSERT done for comparison_id={cid}")
        except Exception as e:
            print(f"[comparison_feed error] {e}")
            traceback.print_exc()
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
                """SELECT CASE_ID AS id FROM TPOPULAR_CASE
                   WHERE (TITLE_A_NM=%s AND TITLE_B_NM=%s) OR (TITLE_A_NM=%s AND TITLE_B_NM=%s)
                   LIMIT 1""",
                (req.company_a_name, req.company_b_name,
                 req.company_b_name, req.company_a_name))
            print(f"[popular_cases] existing={existing}")
            if existing:
                await database.execute(
                    "UPDATE TPOPULAR_CASE SET COMPARISON_NO=COMPARISON_NO+1 WHERE CASE_ID=%s",
                    (existing["id"],))
                print(f"[popular_cases] UPDATE done for id={existing['id']}")
            else:
                points = json.dumps(req.feed_points[:3], ensure_ascii=False) if req.feed_points else '[]'
                await database.execute(
                    """INSERT INTO TPOPULAR_CASE
                       (CASE_TYPE_CD, TITLE_A_NM, TYPE_A_CD, SUB_A_NM, TITLE_B_NM, TYPE_B_CD, SUB_B_NM,
                        POINTS_VAL, VIEW_NO, COMPARISON_NO)
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
            """INSERT INTO TDAILY_STAT (STAT_DT, COMPARISON_NO) VALUES (CURDATE(), 1)
               ON DUPLICATE KEY UPDATE COMPARISON_NO = COMPARISON_NO + 1""")
    except Exception as e:
        print(f"[daily_stats error] {e}")
    # Invalidate feed cache
    cache.delete("landing_feed")
    return {"id": cid}

@router.get("")
async def list_mine(user_id: int = Depends(get_current_user)):
    rows = await database.fetch_all(
        """SELECT COMPARISON_ID AS id, COMP_A_NM AS company_a_name, COMP_A_TP_CD AS type_a,
                  COMP_B_NM AS company_b_name, COMP_B_TP_CD AS type_b,
                  PRIORITY_CD AS priority_key, INS_DTM AS created_at
           FROM TCOMPARISON WHERE MBR_ID=%s ORDER BY INS_DTM DESC LIMIT 50""",
        (user_id,),
    )
    for r in rows:
        if r.get("created_at"):
            r["created_at"] = r["created_at"].isoformat()
    return rows

@router.get("/{comparison_id}")
async def get_one(comparison_id: int, user_id: int = Depends(get_current_user)):
    row = await database.fetch_one(
        """SELECT COMPARISON_ID AS id, MBR_ID AS user_id,
                  COMP_A_NM AS company_a_name, COMP_A_TP_CD AS type_a,
                  SALARY_A_MIN_AMT AS salary_a_min, SALARY_A_MAX_AMT AS salary_a_max,
                  COMMUTE_A_MIN_NO AS commute_a,
                  WORK_STYLE_A_VAL AS work_style_a, BENEFITS_A_VAL AS benefits_a,
                  COMP_B_NM AS company_b_name, COMP_B_TP_CD AS type_b,
                  SALARY_RATE_VAL AS salary_rate, COMMUTE_B_MIN_NO AS commute_b,
                  WORK_STYLE_B_VAL AS work_style_b, BENEFITS_B_VAL AS benefits_b,
                  PRIORITY_CD AS priority_key, SACRIFICE_CD AS sacrifice_key,
                  INS_DTM AS created_at
           FROM TCOMPARISON WHERE COMPARISON_ID=%s AND MBR_ID=%s""",
        (comparison_id, user_id),
    )
    if not row:
        return {"error": "not found"}
    for k in ("work_style_a", "work_style_b", "benefits_a", "benefits_b"):
        if isinstance(row.get(k), str):
            row[k] = json.loads(row[k])
    if row.get("created_at"):
        row["created_at"] = row["created_at"].isoformat()
    return row
