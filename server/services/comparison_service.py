"""비교(comparison) 도메인 서비스.

생성 흐름:
  1) 메인 INSERT (TCOMPARISON) — 실패 시 ValueError. 이것만 성공하면 사용자에겐 성공.
  2) 부가 부수효과 3개 (FEED / POPULAR / DAILY_STAT) — best-effort, 병렬 실행.
     하나가 실패해도 메인은 보존되고, 실패는 구조화 로그로 추적.

라우터(routers/comparisons.py) 는 얇은 wrapper 로 예외만 HTTPException 으로 변환.
"""
import asyncio
import json
import logging

import database
from models.comparison import ComparisonReq
from services import cache

logger = logging.getLogger(__name__)


_COMP_TYPE_LABELS = {
    "large": "대기업", "mid": "중견기업", "public": "공기업",
    "startup": "스타트업", "foreign": "외국계", "freelance": "프리랜서",
}


async def _insert_feed(comparison_id: int, req: ComparisonReq) -> None:
    if not req.feed_headline_ctnt:
        return
    try:
        await database.execute(
            """INSERT INTO TCOMPARISON_FEED
               (COMPARISON_ID, JOB_CTGR_NM, COMP_A_DISP_NM, COMP_A_TP_CD,
                COMP_B_DISP_NM, COMP_B_TP_CD, HEADLINE_CTNT, DETAIL_CTNT,
                METRIC_VAL_CTNT, METRIC_LABEL_NM, METRIC_TYPE_CD)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (comparison_id, req.feed_job_ctgr_nm,
             req.comp_a_nm or "현직", req.comp_a_tp_cd,
             req.comp_b_nm or "이직처", req.comp_b_tp_cd,
             req.feed_headline_ctnt, req.feed_detail_ctnt,
             req.feed_metric_val_ctnt, req.feed_metric_label_nm,
             req.feed_metric_type_cd or "neu"),
        )
        cache.delete("landing_feed")
        logger.info("comparison_feed INSERT done comparison_id=%s", comparison_id)
    except Exception as e:
        logger.exception("comparison_feed INSERT error: %s", e)


async def _upsert_popular(req: ComparisonReq) -> None:
    if not (req.comp_a_nm and req.comp_b_nm):
        logger.debug("popular_cases SKIPPED — company name is None")
        return
    try:
        points = (
            json.dumps(req.feed_points_val[:3], ensure_ascii=False)
            if req.feed_points_val else "[]"
        )
        await database.execute(
            """INSERT INTO TPOPULAR_CASE
               (CASE_TYPE_CD, CURRENT_COMP_NM, CURRENT_COMP_TP_CD, CURRENT_SUB_NM,
                OFFER_COMP_NM, OFFER_COMP_TP_CD, OFFER_SUB_NM,
                POINTS_VAL, VIEW_NO, COMPARISON_NO)
               VALUES ('company',%s,%s,%s,%s,%s,%s,%s,0,1)
               ON DUPLICATE KEY UPDATE COMPARISON_NO = COMPARISON_NO + 1""",
            (req.comp_a_nm, req.comp_a_tp_cd,
             _COMP_TYPE_LABELS.get(req.comp_a_tp_cd, req.comp_a_tp_cd),
             req.comp_b_nm, req.comp_b_tp_cd,
             _COMP_TYPE_LABELS.get(req.comp_b_tp_cd, req.comp_b_tp_cd),
             points),
        )
        cache.delete("landing_popular")
        logger.info("popular_cases UPSERT done: %s vs %s", req.comp_a_nm, req.comp_b_nm)
    except Exception as e:
        logger.exception("popular_cases upsert error: %s", e)


async def _increment_daily_stat() -> None:
    try:
        await database.execute(
            """INSERT INTO TDAILY_STAT (STAT_DT, COMPARISON_NO) VALUES (CURDATE(), 1)
               ON DUPLICATE KEY UPDATE COMPARISON_NO = COMPARISON_NO + 1"""
        )
    except Exception as e:
        logger.warning("daily_stats increment error: %s", e)


async def create_with_side_effects(mbr_id: int, req: ComparisonReq) -> int:
    """TCOMPARISON 생성 + FEED/POPULAR/DAILY_STAT 병렬 부가작업.

    메인 INSERT 실패 시 ValueError. 부가작업은 best-effort 라 실패해도 id 반환.
    """
    try:
        comparison_id = await database.execute(
            """INSERT INTO TCOMPARISON
               (MBR_ID, COMP_A_NM, COMP_A_TP_CD, SALARY_A_MIN_AMT, SALARY_A_MAX_AMT, COMMUTE_A_MIN_NO,
                WORK_STYLE_A_VAL, BENEFITS_A_VAL, COMP_B_NM, COMP_B_TP_CD, SALARY_RATE_VAL, COMMUTE_B_MIN_NO,
                WORK_STYLE_B_VAL, BENEFITS_B_VAL, PRIORITY_CD, SACRIFICE_CD)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (mbr_id, req.comp_a_nm, req.comp_a_tp_cd,
             req.salary_a_min_amt, req.salary_a_max_amt, req.commute_a_min_no,
             json.dumps(req.work_style_a_val, ensure_ascii=False) if req.work_style_a_val else None,
             json.dumps(req.benefits_a_val, ensure_ascii=False) if req.benefits_a_val else None,
             req.comp_b_nm, req.comp_b_tp_cd, req.salary_rate_val, req.commute_b_min_no,
             json.dumps(req.work_style_b_val, ensure_ascii=False) if req.work_style_b_val else None,
             json.dumps(req.benefits_b_val, ensure_ascii=False) if req.benefits_b_val else None,
             req.priority_cd, req.sacrifice_cd),
        )
    except Exception as e:
        logger.exception("TCOMPARISON INSERT error: %s", e)
        raise ValueError("comparison save failed") from e
    if not comparison_id:
        logger.error("TCOMPARISON INSERT returned falsy id: %r", comparison_id)
        raise ValueError("comparison save failed")

    await asyncio.gather(
        _insert_feed(comparison_id, req),
        _upsert_popular(req),
        _increment_daily_stat(),
        return_exceptions=True,
    )
    return comparison_id
