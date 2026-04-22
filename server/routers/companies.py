import json
from fastapi import APIRouter, Depends, HTTPException, Query, status
import database
from services import benefit_service, cache
from models.company import BenefitUpsert, BenefitReportReq
from middleware.auth_middleware import get_optional_user, get_verified_user_for_comp

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
    benefits = await benefit_service.fetch_company_benefits(comp_id)

    ws = comp.get("work_style_val")
    if isinstance(ws, str):
        ws = json.loads(ws)
    comp["work_style_val"] = ws

    return {
        **comp,
        "aliases": [a["alias_nm"] for a in aliases],
        "benefits": benefits,
    }

@router.post("/{comp_id}/benefits/{benefit_id}/report")
async def report_benefit(
    comp_id: int,
    benefit_id: int,
    req: BenefitReportReq,
    reporter_mbr_id: int | None = Depends(get_optional_user),
):
    """복지 값/내용 오류 제보 — 비로그인도 허용. 실제 반영은 관리자 검수 후."""
    if req.report_type_cd == "wrong_amount" and req.reported_amt is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="wrong_amount 제보는 reported_amt 가 필요합니다",
        )
    report_id = await benefit_service.create_report(
        comp_id=comp_id,
        benefit_id=benefit_id,
        report_type_cd=req.report_type_cd,
        reported_amt=req.reported_amt,
        comment_ctnt=req.comment_ctnt,
        reporter_mbr_id=reporter_mbr_id,
    )
    if report_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 회사의 복지 항목을 찾을 수 없습니다",
        )
    return {"report_id": report_id}


@router.put("/{comp_id}/benefits")
async def upsert_benefits(
    comp_id: int,
    items: list[BenefitUpsert],
    user_id: int = Depends(get_verified_user_for_comp),
):
    comp = await database.fetch_one(
        "SELECT COMP_ID AS comp_id FROM TCOMPANY WHERE COMP_ID=%s", (comp_id,)
    )
    if not comp:
        return {"error": "company not found"}

    benefits = await benefit_service.upsert_company_benefits(comp_id, items)
    cache.delete("reference_all")
    return {"count": len(benefits), "benefits": benefits}
