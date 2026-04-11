import json
from fastapi import APIRouter, Depends, Query
import database
from models.company import BenefitUpsert
from middleware.auth_middleware import get_current_user, get_verified_user

router = APIRouter()

@router.get("/search")
async def search(q: str = Query(..., min_length=1)):
    q_like = f"%{q}%"
    rows = await database.fetch_all(
        """SELECT DISTINCT c.COMP_ID AS id, c.COMP_NM AS name, ct.COMP_TP_CD AS type,
                  c.INDUSTRY_NM AS industry, c.LOGO_NM AS logo
           FROM TCOMPANY c
           JOIN TCOMPANY_TYPE ct ON ct.COMP_TP_ID = c.COMP_TP_ID
           LEFT JOIN TCOMPANY_ALIAS ca ON ca.COMP_ID = c.COMP_ID
           WHERE c.COMP_NM LIKE %s OR ca.ALIAS_NM LIKE %s
           LIMIT 20""",
        (q_like, q_like),
    )
    return rows

@router.get("/{company_id}")
async def detail(company_id: int):
    comp = await database.fetch_one(
        """SELECT c.COMP_ID AS id, c.COMP_NM AS name, ct.COMP_TP_CD AS type,
                  c.INDUSTRY_NM AS industry, c.LOGO_NM AS logo, c.WORK_STYLE_VAL AS work_style
           FROM TCOMPANY c JOIN TCOMPANY_TYPE ct ON ct.COMP_TP_ID = c.COMP_TP_ID
           WHERE c.COMP_ID=%s""",
        (company_id,),
    )
    if not comp:
        return {"error": "not found"}

    aliases = await database.fetch_all(
        "SELECT ALIAS_NM AS alias FROM TCOMPANY_ALIAS WHERE COMP_ID=%s", (company_id,)
    )
    benefits = await database.fetch_all(
        """SELECT BENEFIT_CD AS `key`, BENEFIT_NM AS name, BENEFIT_AMT AS val,
                  BENEFIT_CTGR_CD AS cat, BADGE_CD AS badge, NOTE_CTNT AS note,
                  QUAL_YN AS qual, QUAL_DESC_CTNT AS qualText
           FROM TCOMPANY_BENEFIT WHERE COMP_ID=%s ORDER BY SORT_ORDER_NO""",
        (company_id,),
    )

    ws = comp.get("work_style")
    if isinstance(ws, str):
        ws = json.loads(ws)

    return {
        **comp,
        "work_style": ws,
        "aliases": [a["alias"] for a in aliases],
        "benefits": benefits,
    }

@router.put("/{company_id}/benefits")
async def upsert_benefits(company_id: int, items: list[BenefitUpsert], user_id: int = Depends(get_verified_user)):
    comp = await database.fetch_one(
        "SELECT COMP_ID AS id FROM TCOMPANY WHERE COMP_ID=%s", (company_id,)
    )
    if not comp:
        return {"error": "company not found"}

    # 기존 복지 전체 삭제 후 재삽입 (중복 방지)
    await database.execute(
        "DELETE FROM TCOMPANY_BENEFIT WHERE COMP_ID=%s",
        (company_id,),
    )

    for i, b in enumerate(items):
        await database.execute(
            """INSERT INTO TCOMPANY_BENEFIT
               (COMP_ID, BENEFIT_CD, BENEFIT_NM, BENEFIT_AMT, BENEFIT_CTGR_CD, BADGE_CD, NOTE_CTNT, QUAL_YN, QUAL_DESC_CTNT, SORT_ORDER_NO)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               ON DUPLICATE KEY UPDATE
               BENEFIT_NM=VALUES(BENEFIT_NM), BENEFIT_AMT=VALUES(BENEFIT_AMT), BENEFIT_CTGR_CD=VALUES(BENEFIT_CTGR_CD),
               BADGE_CD=VALUES(BADGE_CD), NOTE_CTNT=VALUES(NOTE_CTNT), QUAL_YN=VALUES(QUAL_YN),
               QUAL_DESC_CTNT=VALUES(QUAL_DESC_CTNT), SORT_ORDER_NO=VALUES(SORT_ORDER_NO)""",
            (company_id, b.key, b.name, b.val, b.cat, b.badge,
             b.note, b.qual, b.qualText, b.sortOrder or i),
        )

    benefits = await database.fetch_all(
        """SELECT BENEFIT_CD AS `key`, BENEFIT_NM AS name, BENEFIT_AMT AS val,
                  BENEFIT_CTGR_CD AS cat, BADGE_CD AS badge, NOTE_CTNT AS note,
                  QUAL_YN AS qual, QUAL_DESC_CTNT AS qualText
           FROM TCOMPANY_BENEFIT WHERE COMP_ID=%s ORDER BY SORT_ORDER_NO""",
        (company_id,),
    )
    return {"count": len(benefits), "benefits": benefits}
