"""랜딩 도메인 서비스 — 피드/인기/통계/방문자 카운트.

라우터(routers/landing.py, routers/admin.py) 에서 공통으로 사용.
active_visitors 는 여기 모듈 전역 싱글톤 (프로세스 내 상태) — 스케일아웃 시 P4-1 로 DB 이전.
"""
import json
import logging
import time
from datetime import timezone

import database
from services import cache

logger = logging.getLogger(__name__)


# ━━ Visitor tracking (in-process) ━━
# resume-2026-04-23.md P4-1: 싱글 워커면 유지, --workers 2+ 로 가면 TRATE_LIMIT_BUCKET 또는 Redis 필요.
_active_visitors: dict[str, float] = {}
VISITOR_TTL = 60


def _clean_visitors() -> None:
    now = time.time()
    expired = [k for k, v in _active_visitors.items() if now - v > VISITOR_TTL]
    for k in expired:
        del _active_visitors[k]


def get_active_count() -> int:
    _clean_visitors()
    return len(_active_visitors)


def record_visit(client_id: str) -> None:
    _active_visitors[client_id] = time.time()


# ━━ Feed ━━

async def fetch_feed() -> list[dict]:
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
            r["ins_dtm"] = r["ins_dtm"].replace(tzinfo=timezone.utc).isoformat()
    cache.set("landing_feed", rows, ttl=300)
    return rows


# ━━ Popular cases ━━

async def fetch_popular() -> list[dict]:
    cached = cache.get("landing_popular")
    if cached is not None:
        return cached
    rows = await database.fetch_all(
        """SELECT CASE_ID AS case_id, CASE_TYPE_CD AS case_type_cd,
                  CURRENT_COMP_NM AS current_comp_nm, CURRENT_COMP_TP_CD AS current_comp_tp_cd,
                  CURRENT_SUB_NM AS current_sub_nm,
                  OFFER_COMP_NM AS offer_comp_nm, OFFER_COMP_TP_CD AS offer_comp_tp_cd,
                  OFFER_SUB_NM AS offer_sub_nm,
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


async def increment_case_view(case_id: int) -> int:
    await database.execute(
        "UPDATE TPOPULAR_CASE SET VIEW_NO = VIEW_NO + 1 WHERE CASE_ID = %s",
        (case_id,),
    )
    row = await database.fetch_one(
        "SELECT VIEW_NO AS view_no FROM TPOPULAR_CASE WHERE CASE_ID = %s", (case_id,)
    )
    cache.delete("landing_popular")
    return int(row["view_no"]) if row else 0


# ━━ Stats / Ping ━━

async def _total_comparison_count() -> int:
    row = await database.fetch_one("SELECT COUNT(*) AS cnt FROM TCOMPARISON")
    return int(row["cnt"]) if row else 0


async def _today_comparison_count() -> int:
    row = await database.fetch_one(
        "SELECT COMPARISON_NO AS comparison_no FROM TDAILY_STAT WHERE STAT_DT = CURDATE()"
    )
    return int(row["comparison_no"]) if row else 0


async def fetch_stats() -> dict:
    today = await _today_comparison_count()
    total = await _total_comparison_count()
    return {
        "today_comparison_no": today,
        "total_comparison_no": total,
        "active_visitor_no": get_active_count(),
    }


async def record_ping(client_id: str) -> dict:
    record_visit(client_id)
    total = await _total_comparison_count()
    return {"active_visitor_no": get_active_count(), "total_comparison_no": total}
