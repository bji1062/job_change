"""비교 생성/조회 라우터 — 생성 로직은 services/comparison_service 로 위임."""
import json
import logging

from fastapi import APIRouter, Depends, HTTPException

import database
from middleware.auth_middleware import get_current_user
from models.comparison import ComparisonReq
from services import comparison_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("")
async def create(req: ComparisonReq, mbr_id: int = Depends(get_current_user)):
    try:
        comparison_id = await comparison_service.create_with_side_effects(mbr_id, req)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
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
        raise HTTPException(status_code=404, detail="comparison not found")
    for k in ("work_style_a_val", "work_style_b_val", "benefits_a_val", "benefits_b_val"):
        if isinstance(row.get(k), str):
            row[k] = json.loads(row[k])
    if row.get("ins_dtm"):
        row["ins_dtm"] = row["ins_dtm"].isoformat()
    return row
