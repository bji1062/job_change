import json
import traceback
from fastapi import APIRouter, Depends
import database
from services import cache
from middleware.auth_middleware import get_current_user
from models.comparison import ComparisonReq

router = APIRouter()

@router.post("")
async def create(req: ComparisonReq, mbr_id: int = Depends(get_current_user)):
    try:
        comparison_id = await database.execute(
            """INSERT INTO TCOMPARISON
               (MBR_ID, COMP_A_NM, COMP_A_TP_CD, SALARY_A_MIN_AMT, SALARY_A_MAX_AMT, COMMUTE_A_MIN_NO,
                WORK_STYLE_A_VAL, BENEFITS_A_VAL, COMP_B_NM, COMP_B_TP_CD, SALARY_RATE_VAL, COMMUTE_B_MIN_NO,
                WORK_STYLE_B_VAL, BENEFITS_B_VAL, PRIORITY_CD, SACRIFICE_CD)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (mbr_id, req.comp_a_nm, req.comp_a_tp_cd, req.salary_a_min_amt, req.salary_a_max_amt,
             req.commute_a_min_no,
             json.dumps(req.work_style_a_val, ensure_ascii=False) if req.work_style_a_val else None,
             json.dumps(req.benefits_a_val, ensure_ascii=False) if req.benefits_a_val else None,
             req.comp_b_nm, req.comp_b_tp_cd, req.salary_rate_val, req.commute_b_min_no,
             json.dumps(req.work_style_b_val, ensure_ascii=False) if req.work_style_b_val else None,
             json.dumps(req.benefits_b_val, ensure_ascii=False) if req.benefits_b_val else None,
             req.priority_cd, req.sacrifice_cd),
        )
    except Exception as e:
        print(f"[comparisons INSERT error] {e}")
        traceback.print_exc()
        return {"error": "comparison save failed"}
    if not comparison_id:
        print(f"[comparisons] WARNING: comparison_id is {comparison_id!r}")
        return {"error": "comparison save failed"}
    # Feed auto-generation
    if req.feed_headline_ctnt:
        try:
            await database.execute(
                """INSERT INTO TCOMPARISON_FEED
                   (COMPARISON_ID, JOB_CTGR_NM, COMP_A_DISP_NM, COMP_A_TP_CD,
                    COMP_B_DISP_NM, COMP_B_TP_CD, HEADLINE_CTNT, DETAIL_CTNT,
                    METRIC_VAL_CTNT, METRIC_LABEL_NM, METRIC_TYPE_CD)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (comparison_id, req.feed_job_ctgr_nm, req.comp_a_nm or '현직', req.comp_a_tp_cd,
                 req.comp_b_nm or '이직처', req.comp_b_tp_cd, req.feed_headline_ctnt,
                 req.feed_detail_ctnt, req.feed_metric_val_ctnt, req.feed_metric_label_nm,
                 req.feed_metric_type_cd or 'neu'))
            print(f"[comparison_feed] INSERT done for comparison_id={comparison_id}")
        except Exception as e:
            print(f"[comparison_feed error] {e}")
            traceback.print_exc()
    # Auto-upsert into TPOPULAR_CASE
    print(f"[popular_cases] comp_a_nm={req.comp_a_nm!r}, comp_b_nm={req.comp_b_nm!r}")
    if req.comp_a_nm and req.comp_b_nm:
        try:
            type_labels = {
                'large': '대기업', 'mid': '중견기업', 'public': '공기업',
                'startup': '스타트업', 'foreign': '외국계', 'freelance': '프리랜서'
            }
            # Check if this pair already exists (A vs B or B vs A)
            existing = await database.fetch_one(
                """SELECT CASE_ID AS case_id FROM TPOPULAR_CASE
                   WHERE (TITLE_A_NM=%s AND TITLE_B_NM=%s) OR (TITLE_A_NM=%s AND TITLE_B_NM=%s)
                   LIMIT 1""",
                (req.comp_a_nm, req.comp_b_nm,
                 req.comp_b_nm, req.comp_a_nm))
            print(f"[popular_cases] existing={existing}")
            if existing:
                await database.execute(
                    "UPDATE TPOPULAR_CASE SET COMPARISON_NO=COMPARISON_NO+1 WHERE CASE_ID=%s",
                    (existing["case_id"],))
                print(f"[popular_cases] UPDATE done for case_id={existing['case_id']}")
            else:
                points = json.dumps(req.feed_points_val[:3], ensure_ascii=False) if req.feed_points_val else '[]'
                await database.execute(
                    """INSERT INTO TPOPULAR_CASE
                       (CASE_TYPE_CD, TITLE_A_NM, TYPE_A_CD, SUB_A_NM, TITLE_B_NM, TYPE_B_CD, SUB_B_NM,
                        POINTS_VAL, VIEW_NO, COMPARISON_NO)
                       VALUES ('company',%s,%s,%s,%s,%s,%s,%s,0,1)""",
                    (req.comp_a_nm, req.comp_a_tp_cd, type_labels.get(req.comp_a_tp_cd, req.comp_a_tp_cd),
                     req.comp_b_nm, req.comp_b_tp_cd, type_labels.get(req.comp_b_tp_cd, req.comp_b_tp_cd),
                     points))
                print(f"[popular_cases] INSERT done: {req.comp_a_nm} vs {req.comp_b_nm}")
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
    return {"comparison_id": comparison_id}

@router.get("")
async def list_mine(mbr_id: int = Depends(get_current_user)):
    rows = await database.fetch_all(
        """SELECT COMPARISON_ID AS comparison_id, COMP_A_NM AS comp_a_nm, COMP_A_TP_CD AS comp_a_tp_cd,
                  COMP_B_NM AS comp_b_nm, COMP_B_TP_CD AS comp_b_tp_cd,
                  PRIORITY_CD AS priority_cd, INS_DTM AS ins_dtm
           FROM TCOMPARISON WHERE MBR_ID=%s ORDER BY INS_DTM DESC LIMIT 50""",
        (mbr_id,),
    )
    for r in rows:
        if r.get("ins_dtm"):
            r["ins_dtm"] = r["ins_dtm"].isoformat()
    return rows

@router.get("/{comparison_id}")
async def get_one(comparison_id: int, mbr_id: int = Depends(get_current_user)):
    row = await database.fetch_one(
        """SELECT COMPARISON_ID AS comparison_id, MBR_ID AS mbr_id,
                  COMP_A_NM AS comp_a_nm, COMP_A_TP_CD AS comp_a_tp_cd,
                  SALARY_A_MIN_AMT AS salary_a_min_amt, SALARY_A_MAX_AMT AS salary_a_max_amt,
                  COMMUTE_A_MIN_NO AS commute_a_min_no,
                  WORK_STYLE_A_VAL AS work_style_a_val, BENEFITS_A_VAL AS benefits_a_val,
                  COMP_B_NM AS comp_b_nm, COMP_B_TP_CD AS comp_b_tp_cd,
                  SALARY_RATE_VAL AS salary_rate_val, COMMUTE_B_MIN_NO AS commute_b_min_no,
                  WORK_STYLE_B_VAL AS work_style_b_val, BENEFITS_B_VAL AS benefits_b_val,
                  PRIORITY_CD AS priority_cd, SACRIFICE_CD AS sacrifice_cd,
                  INS_DTM AS ins_dtm
           FROM TCOMPARISON WHERE COMPARISON_ID=%s AND MBR_ID=%s""",
        (comparison_id, mbr_id),
    )
    if not row:
        return {"error": "not found"}
    for k in ("work_style_a_val", "work_style_b_val", "benefits_a_val", "benefits_b_val"):
        if isinstance(row.get(k), str):
            row[k] = json.loads(row[k])
    if row.get("ins_dtm"):
        row["ins_dtm"] = row["ins_dtm"].isoformat()
    return row
