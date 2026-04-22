"""복지(benefit) 도메인 공용 로직 — TTL, 만료 계산, 승격 로그.

라우터(companies.py, admin.py) 양쪽에서 재사용하는 헬퍼를 모음.
Phase 1 은 TTL/만료 계산과 승격 API 지원에 한정. Phase 4(만료 cron)/Phase 5(사용자 제보)
에서 이 모듈에 로직을 더 얹는다 — resume-2026-04-23.md 참조.
"""
from datetime import datetime, timedelta
from typing import Optional

import database


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 카테고리별 TTL (일 단위)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 결정 기준: 해당 카테고리의 '제도 변경 빈도' — 빠르게 바뀌는 것은 TTL 짧게.
#   flexibility (재택/유연근무): 회사 정책 변경 잦음, 6개월
#   compensation (성과급/보너스): 연 1회 개편 많음, 1년
#   work_env/time_off: 안정적, 1.5년
#   health/family: 제도 자체가 안정적, 2년
#   growth/leisure/perks: 중간, 1년
# schema.sql TCOMPANY_BENEFIT.BENEFIT_CTGR_CD COMMENT 의 9종과 매핑.
BADGE_TTL_DAYS: dict[str, int] = {
    "flexibility": 180,
    "compensation": 365,
    "work_env": 540,
    "time_off": 540,
    "health": 730,
    "family": 730,
    "growth": 365,
    "leisure": 365,
    "perks": 365,
}

# 매핑되지 않은 카테고리에 대한 보수적 기본값
DEFAULT_TTL_DAYS = 365


def ttl_for_category(ctgr_cd: Optional[str]) -> int:
    """카테고리 코드 → TTL 일수. 미등록 카테고리는 DEFAULT_TTL_DAYS."""
    if not ctgr_cd:
        return DEFAULT_TTL_DAYS
    return BADGE_TTL_DAYS.get(ctgr_cd, DEFAULT_TTL_DAYS)


def calc_expires_dtm(verified_dtm: datetime, ctgr_cd: Optional[str]) -> datetime:
    """VERIFIED_DTM + 카테고리 TTL → EXPIRES_DTM."""
    return verified_dtm + timedelta(days=ttl_for_category(ctgr_cd))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 승격/강등 로그 기록
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def log_badge_action(
    benefit_id: int,
    actor_mbr_id: int,
    action_cd: str,
    from_badge_cd: Optional[str],
    to_badge_cd: Optional[str],
    note_ctnt: Optional[str] = None,
) -> int:
    """TCOMPANY_BENEFIT_BADGE_LOG 에 감사 행 1건 기록.

    action_cd: 'promote' | 'demote' | 'verify' — 마이그레이션 COMMENT 와 동기화.
    호출자는 이미 대상 benefit_id 존재를 확인했다고 가정.
    """
    return await database.execute(
        """INSERT INTO TCOMPANY_BENEFIT_BADGE_LOG
           (BENEFIT_ID, ACTOR_MBR_ID, ACTION_CD, FROM_BADGE_CD, TO_BADGE_CD, NOTE_CTNT)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (benefit_id, actor_mbr_id, action_cd, from_badge_cd, to_badge_cd, note_ctnt),
    )


async def promote_to_official(
    benefit_id: int,
    actor_mbr_id: int,
    note_ctnt: Optional[str] = None,
) -> dict:
    """est → official 승격. VERIFIED_DTM/BY/EXPIRES_DTM 동시 갱신 + 로그 기록.

    반환: 승격 후 행 (관리자 UI 즉시 리렌더용).
    존재하지 않으면 None 반환 — 라우터에서 404 처리.
    """
    row = await database.fetch_one(
        """SELECT BENEFIT_ID AS benefit_id, BADGE_CD AS badge_cd,
                  BENEFIT_CTGR_CD AS benefit_ctgr_cd
           FROM TCOMPANY_BENEFIT WHERE BENEFIT_ID=%s""",
        (benefit_id,),
    )
    if not row:
        return None
    now = datetime.now()
    expires_dtm = calc_expires_dtm(now, row.get("benefit_ctgr_cd"))
    from_badge_cd = row.get("badge_cd") or "est"

    async with database.transaction() as tx:
        await tx.execute(
            """UPDATE TCOMPANY_BENEFIT
               SET BADGE_CD='official', VERIFIED_DTM=%s, VERIFIED_BY_ID=%s, EXPIRES_DTM=%s
               WHERE BENEFIT_ID=%s""",
            (now, actor_mbr_id, expires_dtm, benefit_id),
        )
        await tx.execute(
            """INSERT INTO TCOMPANY_BENEFIT_BADGE_LOG
               (BENEFIT_ID, ACTOR_MBR_ID, ACTION_CD, FROM_BADGE_CD, TO_BADGE_CD, NOTE_CTNT)
               VALUES (%s, %s, 'promote', %s, 'official', %s)""",
            (benefit_id, actor_mbr_id, from_badge_cd, note_ctnt),
        )
    return {
        "benefit_id": benefit_id,
        "badge_cd": "official",
        "verified_dtm": now.isoformat(),
        "expires_dtm": expires_dtm.isoformat(),
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 회사별 복지 CRUD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# admin.py (관리자 전체 교체) 와 companies.py (회사 이메일 인증 사용자) 양쪽에서 쓰던
# 동일한 DELETE+INSERT 루프를 한 곳으로 수렴. 두 라우터는 이제 thin wrapper.

# 사용자/관리자 입력 복지에서 공통으로 꺼낼 필드 — Pydantic 모델(BenefitItem/BenefitUpsert) 호환.
_BEN_FIELDS = (
    "benefit_cd", "benefit_nm", "benefit_amt", "benefit_ctgr_cd",
    "badge_cd", "badge_src_cd", "badge_src_url_ctnt",
    "note_ctnt", "qual_yn", "qual_desc_ctnt", "sort_order_no",
)


def _as_dict(item) -> dict:
    """Pydantic v2 / v1 / dict 모두 허용."""
    if hasattr(item, "model_dump"):
        return item.model_dump()
    if hasattr(item, "dict"):
        return item.dict()
    return dict(item)


async def fetch_company_benefits(comp_id: int) -> list[dict]:
    """회사 복지 목록 — badge 메타 + 감사 필드 포함. datetime ISO 직렬화."""
    rows = await database.fetch_all(
        """SELECT BENEFIT_ID AS benefit_id, BENEFIT_CD AS benefit_cd, BENEFIT_NM AS benefit_nm,
                  BENEFIT_AMT AS benefit_amt, BENEFIT_CTGR_CD AS benefit_ctgr_cd,
                  BADGE_CD AS badge_cd, BADGE_SRC_CD AS badge_src_cd,
                  BADGE_SRC_URL_CTNT AS badge_src_url_ctnt,
                  VERIFIED_DTM AS verified_dtm, EXPIRES_DTM AS expires_dtm,
                  NOTE_CTNT AS note_ctnt,
                  QUAL_YN AS qual_yn, QUAL_DESC_CTNT AS qual_desc_ctnt,
                  SORT_ORDER_NO AS sort_order_no
           FROM TCOMPANY_BENEFIT WHERE COMP_ID=%s ORDER BY SORT_ORDER_NO""",
        (comp_id,),
    )
    for r in rows:
        r["qual_yn"] = bool(r.get("qual_yn"))
        for k in ("verified_dtm", "expires_dtm"):
            if r.get(k) and hasattr(r[k], "isoformat"):
                r[k] = r[k].isoformat()
    return rows


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 사용자 제보 (TBENEFIT_REPORT)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def create_report(
    comp_id: int,
    benefit_id: int,
    report_type_cd: str,
    reported_amt: Optional[int],
    comment_ctnt: Optional[str],
    reporter_mbr_id: Optional[int],
) -> Optional[int]:
    """사용자 "값 틀림" 제보 저장. 대상 benefit 가 해당 comp_id 에 속해야 함.

    반환: 저장된 REPORT_ID. 대상이 없으면 None (라우터에서 404).
    익명 제보 허용 — reporter_mbr_id 는 NULL 가능.
    """
    row = await database.fetch_one(
        "SELECT BENEFIT_ID FROM TCOMPANY_BENEFIT WHERE BENEFIT_ID=%s AND COMP_ID=%s",
        (benefit_id, comp_id),
    )
    if not row:
        return None
    return await database.execute(
        """INSERT INTO TBENEFIT_REPORT
           (BENEFIT_ID, REPORTER_MBR_ID, REPORT_TYPE_CD, REPORTED_AMT, COMMENT_CTNT, STATUS_CD)
           VALUES (%s, %s, %s, %s, %s, 'open')""",
        (benefit_id, reporter_mbr_id, report_type_cd, reported_amt, comment_ctnt),
    )


async def list_open_reports(limit: int = 50) -> list[dict]:
    """관리자 검수 큐 — 미해결 제보 + 복지 컨텍스트 조인. INS_DTM 역순."""
    rows = await database.fetch_all(
        f"""SELECT br.REPORT_ID AS report_id, br.BENEFIT_ID AS benefit_id,
                   br.REPORTER_MBR_ID AS reporter_mbr_id,
                   br.REPORT_TYPE_CD AS report_type_cd,
                   br.REPORTED_AMT AS reported_amt, br.COMMENT_CTNT AS comment_ctnt,
                   br.INS_DTM AS ins_dtm,
                   cb.BENEFIT_CD AS benefit_cd, cb.BENEFIT_NM AS benefit_nm,
                   cb.BENEFIT_AMT AS current_amt, cb.BADGE_CD AS badge_cd,
                   c.COMP_ID AS comp_id, c.COMP_NM AS comp_nm,
                   m.EMAIL_ADDR AS reporter_email
            FROM TBENEFIT_REPORT br
            JOIN TCOMPANY_BENEFIT cb ON cb.BENEFIT_ID = br.BENEFIT_ID
            JOIN TCOMPANY c ON c.COMP_ID = cb.COMP_ID
            LEFT JOIN TMEMBER m ON m.MBR_ID = br.REPORTER_MBR_ID
            WHERE br.STATUS_CD = 'open'
            ORDER BY br.INS_DTM DESC
            LIMIT %s""",
        (limit,),
    )
    for r in rows:
        if r.get("ins_dtm") and hasattr(r["ins_dtm"], "isoformat"):
            r["ins_dtm"] = r["ins_dtm"].isoformat()
    return rows


async def resolve_report(
    report_id: int,
    actor_mbr_id: int,
    status_cd: str,  # 'resolved' | 'rejected'
    note_ctnt: Optional[str] = None,
) -> Optional[dict]:
    """제보 처리 — STATUS_CD 변경 + 처리 메타 기록. 반영(resolved) 시 BENEFIT_AMT 까지 갱신하진 않음 — 관리자가 복지 편집 화면에서 수동 반영."""
    row = await database.fetch_one(
        "SELECT REPORT_ID, STATUS_CD FROM TBENEFIT_REPORT WHERE REPORT_ID=%s",
        (report_id,),
    )
    if not row:
        return None
    await database.execute(
        """UPDATE TBENEFIT_REPORT
           SET STATUS_CD=%s, RESOLVED_BY_ID=%s, RESOLVED_DTM=NOW(), RESOLVE_NOTE_CTNT=%s
           WHERE REPORT_ID=%s""",
        (status_cd, actor_mbr_id, note_ctnt, report_id),
    )
    return {"report_id": report_id, "status_cd": status_cd}


async def upsert_company_benefits(comp_id: int, items: list) -> list[dict]:
    """회사 복지 전체 교체(clean slate: DELETE + INSERT).

    BADGE_SRC_CD / BADGE_SRC_URL_CTNT 까지 반영 — 기존 라우터의 누락 필드를 함께 정상화.
    반환: 저장 후 최신 복지 목록 (프론트 즉시 렌더용).
    """
    async with database.transaction() as tx:
        await tx.execute("DELETE FROM TCOMPANY_BENEFIT WHERE COMP_ID=%s", (comp_id,))
        for i, item in enumerate(items):
            b = _as_dict(item)
            sort_order_no = b.get("sort_order_no") or i
            await tx.execute(
                """INSERT INTO TCOMPANY_BENEFIT
                   (COMP_ID, BENEFIT_CD, BENEFIT_NM, BENEFIT_AMT, BENEFIT_CTGR_CD,
                    BADGE_CD, BADGE_SRC_CD, BADGE_SRC_URL_CTNT,
                    NOTE_CTNT, QUAL_YN, QUAL_DESC_CTNT, SORT_ORDER_NO)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    comp_id,
                    b.get("benefit_cd"),
                    b.get("benefit_nm"),
                    b.get("benefit_amt") or 0,
                    b.get("benefit_ctgr_cd"),
                    b.get("badge_cd") or "est",
                    b.get("badge_src_cd"),
                    b.get("badge_src_url_ctnt"),
                    b.get("note_ctnt"),
                    bool(b.get("qual_yn")),
                    b.get("qual_desc_ctnt"),
                    sort_order_no,
                ),
            )
    return await fetch_company_benefits(comp_id)
