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
        """SELECT DISTINCT c.COMP_ID AS comp_id, c.COMP_NM AS comp_nm,
                  ct.COMP_TP_CD AS comp_tp_cd,
                  c.INDUSTRY_NM AS industry_nm, c.LOGO_NM AS logo_nm
           FROM TCOMPANY c
           JOIN TCOMPANY_TYPE ct ON ct.COMP_TP_ID = c.COMP_TP_ID
           LEFT JOIN TCOMPANY_ALIAS ca ON ca.COMP_ID = c.COMP_ID
           WHERE c.COMP_NM LIKE %s OR ca.ALIAS_NM LIKE %s
           LIMIT 20""",
        (q_like, q_like),
    )
    return rows

@router.get("/{comp_id}")
async def detail(comp_id: int):
    comp = await database.fetch_one(
        """SELECT c.COMP_ID AS comp_id, c.COMP_NM AS comp_nm,
                  ct.COMP_TP_CD AS comp_tp_cd,
                  c.INDUSTRY_NM AS industry_nm, c.LOGO_NM AS logo_nm,
                  c.WORK_STYLE_VAL AS work_style_val
           FROM TCOMPANY c JOIN TCOMPANY_TYPE ct ON ct.COMP_TP_ID = c.COMP_TP_ID
           WHERE c.COMP_ID=%s""",
        (comp_id,),
    )
    if not comp:
        return {"error": "not found"}

    aliases = await database.fetch_all(
        "SELECT ALIAS_NM AS alias_nm FROM TCOMPANY_ALIAS WHERE COMP_ID=%s", (comp_id,)
    )
    benefits = await database.fetch_all(
        """SELECT BENEFIT_CD AS benefit_cd, BENEFIT_NM AS benefit_nm,
                  BENEFIT_AMT AS benefit_amt, BENEFIT_CTGR_CD AS benefit_ctgr_cd,
                  BADGE_CD AS badge_cd, NOTE_CTNT AS note_ctnt,
                  QUAL_YN AS qual_yn, QUAL_DESC_CTNT AS qual_desc_ctnt
           FROM TCOMPANY_BENEFIT WHERE COMP_ID=%s ORDER BY SORT_ORDER_NO""",
        (comp_id,),
    )

    ws = comp.get("work_style_val")
    if isinstance(ws, str):
        ws = json.loads(ws)
    comp["work_style_val"] = ws

    for b in benefits:
        b["qual_yn"] = bool(b.get("qual_yn"))

    return {
        **comp,
        "aliases": [a["alias_nm"] for a in aliases],
        "benefits": benefits,
    }

@router.put("/{comp_id}/benefits")
async def upsert_benefits(comp_id: int, items: list[BenefitUpsert], user_id: int = Depends(get_verified_user)):
    comp = await database.fetch_one(
        "SELECT COMP_ID AS comp_id FROM TCOMPANY WHERE COMP_ID=%s", (comp_id,)
    )
    if not comp:
        return {"error": "company not found"}

    await database.execute(
        "DELETE FROM TCOMPANY_BENEFIT WHERE COMP_ID=%s",
        (comp_id,),
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
            (comp_id, b.benefit_cd, b.benefit_nm, b.benefit_amt, b.benefit_ctgr_cd, b.badge_cd,
             b.note_ctnt, b.qual_yn, b.qual_desc_ctnt, b.sort_order_no or i),
        )

    benefits = await database.fetch_all(
        """SELECT BENEFIT_CD AS benefit_cd, BENEFIT_NM AS benefit_nm,
                  BENEFIT_AMT AS benefit_amt, BENEFIT_CTGR_CD AS benefit_ctgr_cd,
                  BADGE_CD AS badge_cd, NOTE_CTNT AS note_ctnt,
                  QUAL_YN AS qual_yn, QUAL_DESC_CTNT AS qual_desc_ctnt
           FROM TCOMPANY_BENEFIT WHERE COMP_ID=%s ORDER BY SORT_ORDER_NO""",
        (comp_id,),
    )
    for b in benefits:
        b["qual_yn"] = bool(b.get("qual_yn"))
    return {"count": len(benefits), "benefits": benefits}
