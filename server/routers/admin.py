import json
import time
from fastapi import APIRouter, Depends, HTTPException, Query, status
import database
from services import cache
from middleware.auth_middleware import get_admin_user
from models.admin import (
    DashboardStats, CompanyCreate, CompanyUpdate, BenefitItem,
    AliasUpdate, PopularCaseReq, UserRoleUpdate, PagedResponse,
)

router = APIRouter()

# ━━ DASHBOARD ━━

@router.get("/dashboard", response_model=DashboardStats)
async def dashboard(admin_id: int = Depends(get_admin_user)):
    total_mbr = await database.fetch_one("SELECT COUNT(*) AS cnt FROM TMEMBER")
    today_mbr = await database.fetch_one(
        "SELECT COUNT(*) AS cnt FROM TMEMBER WHERE DATE(INS_DTM) = CURDATE()"
    )
    total_comparison = await database.fetch_one("SELECT COUNT(*) AS cnt FROM TCOMPARISON")
    today_comparison = await database.fetch_one(
        "SELECT COMPARISON_NO AS cnt FROM TDAILY_STAT WHERE STAT_DT = CURDATE()"
    )
    total_comp = await database.fetch_one("SELECT COUNT(*) AS cnt FROM TCOMPANY")
    comp_with_ben = await database.fetch_one(
        "SELECT COUNT(DISTINCT COMP_ID) AS cnt FROM TCOMPANY_BENEFIT"
    )
    from routers.landing import _get_active_count
    return DashboardStats(
        total_mbr_no=int(total_mbr["cnt"]) if total_mbr else 0,
        today_mbr_no=int(today_mbr["cnt"]) if today_mbr else 0,
        total_comparison_no=int(total_comparison["cnt"]) if total_comparison else 0,
        today_comparison_no=int(today_comparison["cnt"]) if today_comparison else 0,
        total_comp_no=int(total_comp["cnt"]) if total_comp else 0,
        comp_with_benefit_no=int(comp_with_ben["cnt"]) if comp_with_ben else 0,
        active_visitor_no=_get_active_count(),
    )

# ━━ MEMBERS ━━

@router.get("/members", response_model=PagedResponse)
async def list_members(
    page: int = Query(1, ge=1),
    q: str = Query("", max_length=100),
    admin_id: int = Depends(get_admin_user),
):
    page_size = 20
    offset = (page - 1) * page_size
    select_cols = ("MBR_ID AS mbr_id, EMAIL_ADDR AS email_addr, MBR_NM AS mbr_nm, "
                   "ROLE_CD AS role_cd, JOB_NM AS job_nm, INS_DTM AS ins_dtm")
    if q:
        where = "WHERE EMAIL_ADDR LIKE %s OR MBR_NM LIKE %s"
        like = f"%{q}%"
        args = (like, like)
        count_row = await database.fetch_one(
            f"SELECT COUNT(*) AS cnt FROM TMEMBER {where}", args
        )
        rows = await database.fetch_all(
            f"SELECT {select_cols} FROM TMEMBER {where} ORDER BY INS_DTM DESC LIMIT %s OFFSET %s",
            (*args, page_size, offset),
        )
    else:
        count_row = await database.fetch_one("SELECT COUNT(*) AS cnt FROM TMEMBER")
        rows = await database.fetch_all(
            f"SELECT {select_cols} FROM TMEMBER ORDER BY INS_DTM DESC LIMIT %s OFFSET %s",
            (page_size, offset),
        )
    for r in rows:
        if r.get("ins_dtm"):
            r["ins_dtm"] = r["ins_dtm"].isoformat()
    return PagedResponse(
        items=rows,
        total=int(count_row["cnt"]) if count_row else 0,
        page=page,
        page_size=page_size,
    )

@router.put("/members/{mbr_id}/role")
async def update_member_role(
    mbr_id: int,
    req: UserRoleUpdate,
    admin_id: int = Depends(get_admin_user),
):
    if mbr_id == admin_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot change own role")
    user = await database.fetch_one("SELECT MBR_ID AS mbr_id FROM TMEMBER WHERE MBR_ID=%s", (mbr_id,))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    await database.execute("UPDATE TMEMBER SET ROLE_CD=%s WHERE MBR_ID=%s", (req.role_cd, mbr_id))
    return {"ok": True}

# ━━ COMPANIES ━━

@router.get("/companies", response_model=PagedResponse)
async def list_companies(
    page: int = Query(1, ge=1),
    q: str = Query("", max_length=100),
    comp_tp_cd: str = Query("", max_length=20),
    admin_id: int = Depends(get_admin_user),
):
    page_size = 20
    offset = (page - 1) * page_size
    conditions = []
    args = []
    if q:
        conditions.append("c.COMP_NM LIKE %s")
        args.append(f"%{q}%")
    if comp_tp_cd:
        conditions.append("ct.COMP_TP_CD = %s")
        args.append(comp_tp_cd)
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    count_row = await database.fetch_one(
        f"""SELECT COUNT(*) AS cnt FROM TCOMPANY c
            JOIN TCOMPANY_TYPE ct ON ct.COMP_TP_ID = c.COMP_TP_ID {where}""",
        tuple(args),
    )
    rows = await database.fetch_all(
        f"""SELECT c.COMP_ID AS comp_id, c.COMP_NM AS comp_nm, ct.COMP_TP_CD AS comp_tp_cd,
                   c.INDUSTRY_NM AS industry_nm,
                   COALESCE(b.ben_cnt, 0) AS benefit_no,
                   COALESCE(a.alias_cnt, 0) AS alias_no
            FROM TCOMPANY c
            JOIN TCOMPANY_TYPE ct ON ct.COMP_TP_ID = c.COMP_TP_ID
            LEFT JOIN (SELECT COMP_ID, COUNT(*) AS ben_cnt FROM TCOMPANY_BENEFIT GROUP BY COMP_ID) b ON b.COMP_ID = c.COMP_ID
            LEFT JOIN (SELECT COMP_ID, COUNT(*) AS alias_cnt FROM TCOMPANY_ALIAS GROUP BY COMP_ID) a ON a.COMP_ID = c.COMP_ID
            {where}
            ORDER BY c.COMP_NM
            LIMIT %s OFFSET %s""",
        (*args, page_size, offset),
    )
    return PagedResponse(
        items=rows,
        total=int(count_row["cnt"]) if count_row else 0,
        page=page,
        page_size=page_size,
    )

async def _resolve_comp_tp_id(comp_tp_cd: str) -> int | None:
    """COMP_TP_CD 문자열 코드를 INT PK로 변환."""
    row = await database.fetch_one(
        "SELECT COMP_TP_ID AS comp_tp_id FROM TCOMPANY_TYPE WHERE COMP_TP_CD=%s", (comp_tp_cd,)
    )
    return row["comp_tp_id"] if row else None


@router.post("/companies")
async def create_company(req: CompanyCreate, admin_id: int = Depends(get_admin_user)):
    existing = await database.fetch_one("SELECT COMP_ID AS comp_id FROM TCOMPANY WHERE COMP_NM=%s", (req.comp_nm,))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Company name already exists")
    # COMP_ENG_NM 슬러그 생성
    comp_eng_nm = req.comp_nm.lower().replace(" ", "_")[:30]
    existing_eng = await database.fetch_one("SELECT COMP_ID AS comp_id FROM TCOMPANY WHERE COMP_ENG_NM=%s", (comp_eng_nm,))
    if existing_eng:
        import time as _t
        comp_eng_nm = f"{comp_eng_nm[:24]}_{int(_t.time()) % 100000}"
    tp_id = await _resolve_comp_tp_id(req.comp_tp_cd)
    if not tp_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown company type")
    work_style_json = json.dumps(req.work_style_val, ensure_ascii=False) if req.work_style_val else None
    comp_id = await database.execute(
        """INSERT INTO TCOMPANY (COMP_ENG_NM, COMP_NM, COMP_TP_ID, INDUSTRY_NM, LOGO_NM, WORK_STYLE_VAL, CAREERS_BENEFIT_URL)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (comp_eng_nm, req.comp_nm, tp_id, req.industry_nm, req.logo_nm, work_style_json, req.careers_benefit_url),
    )
    cache.delete("reference_all")
    return {"comp_id": comp_id}

@router.put("/companies/{comp_id}")
async def update_company(comp_id: int, req: CompanyUpdate, admin_id: int = Depends(get_admin_user)):
    existing = await database.fetch_one("SELECT COMP_ID AS comp_id FROM TCOMPANY WHERE COMP_ID=%s", (comp_id,))
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    sets = []
    args = []
    if req.comp_nm is not None:
        sets.append("COMP_NM=%s")
        args.append(req.comp_nm)
    if req.comp_tp_cd is not None:
        tp_id = await _resolve_comp_tp_id(req.comp_tp_cd)
        if not tp_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown company type")
        sets.append("COMP_TP_ID=%s")
        args.append(tp_id)
    if req.industry_nm is not None:
        sets.append("INDUSTRY_NM=%s")
        args.append(req.industry_nm)
    if req.logo_nm is not None:
        sets.append("LOGO_NM=%s")
        args.append(req.logo_nm)
    if req.work_style_val is not None:
        sets.append("WORK_STYLE_VAL=%s")
        args.append(json.dumps(req.work_style_val, ensure_ascii=False))
    if req.careers_benefit_url is not None:
        sets.append("CAREERS_BENEFIT_URL=%s")
        args.append(req.careers_benefit_url)
    if not sets:
        return {"ok": True}
    args.append(comp_id)
    await database.execute(
        f"UPDATE TCOMPANY SET {', '.join(sets)} WHERE COMP_ID=%s", tuple(args)
    )
    cache.delete("reference_all")
    return {"ok": True}

@router.delete("/companies/{comp_id}")
async def delete_company(comp_id: int, admin_id: int = Depends(get_admin_user)):
    existing = await database.fetch_one("SELECT COMP_ID AS comp_id FROM TCOMPANY WHERE COMP_ID=%s", (comp_id,))
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    await database.execute("DELETE FROM TCOMPANY WHERE COMP_ID=%s", (comp_id,))
    cache.delete("reference_all")
    return {"ok": True}

# ━━ COMPANY BENEFITS ━━

@router.get("/companies/{comp_id}/benefits")
async def get_company_benefits(comp_id: int, admin_id: int = Depends(get_admin_user)):
    rows = await database.fetch_all(
        """SELECT BENEFIT_ID AS benefit_id, BENEFIT_CD AS benefit_cd, BENEFIT_NM AS benefit_nm,
                  BENEFIT_AMT AS benefit_amt, BENEFIT_CTGR_CD AS benefit_ctgr_cd,
                  BADGE_CD AS badge_cd, NOTE_CTNT AS note_ctnt,
                  QUAL_YN AS qual_yn, QUAL_DESC_CTNT AS qual_desc_ctnt,
                  SORT_ORDER_NO AS sort_order_no
           FROM TCOMPANY_BENEFIT WHERE COMP_ID=%s ORDER BY SORT_ORDER_NO""",
        (comp_id,),
    )
    for r in rows:
        r["qual_yn"] = bool(r.get("qual_yn"))
    return rows

@router.put("/companies/{comp_id}/benefits")
async def save_company_benefits(
    comp_id: int,
    benefits: list[BenefitItem],
    admin_id: int = Depends(get_admin_user),
):
    existing = await database.fetch_one("SELECT COMP_ID AS comp_id FROM TCOMPANY WHERE COMP_ID=%s", (comp_id,))
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    await database.execute("DELETE FROM TCOMPANY_BENEFIT WHERE COMP_ID=%s", (comp_id,))
    for i, b in enumerate(benefits):
        await database.execute(
            """INSERT INTO TCOMPANY_BENEFIT
               (COMP_ID, BENEFIT_CD, BENEFIT_NM, BENEFIT_AMT, BENEFIT_CTGR_CD, BADGE_CD, NOTE_CTNT, QUAL_YN, QUAL_DESC_CTNT, SORT_ORDER_NO)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (comp_id, b.benefit_cd, b.benefit_nm, b.benefit_amt,
             b.benefit_ctgr_cd, b.badge_cd, b.note_ctnt,
             b.qual_yn, b.qual_desc_ctnt, b.sort_order_no or i),
        )
    cache.delete("reference_all")
    return {"ok": True, "count": len(benefits)}

# ━━ COMPANY ALIASES ━━

@router.put("/companies/{comp_id}/aliases")
async def save_company_aliases(
    comp_id: int,
    req: AliasUpdate,
    admin_id: int = Depends(get_admin_user),
):
    existing = await database.fetch_one("SELECT COMP_ID AS comp_id FROM TCOMPANY WHERE COMP_ID=%s", (comp_id,))
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    await database.execute("DELETE FROM TCOMPANY_ALIAS WHERE COMP_ID=%s", (comp_id,))
    for alias_nm in req.aliases:
        if alias_nm.strip():
            await database.execute(
                "INSERT INTO TCOMPANY_ALIAS (COMP_ID, ALIAS_NM) VALUES (%s, %s)",
                (comp_id, alias_nm.strip()),
            )
    cache.delete("reference_all")
    return {"ok": True, "count": len(req.aliases)}

# ━━ POPULAR CASES ━━

@router.get("/popular-cases")
async def list_popular_cases(admin_id: int = Depends(get_admin_user)):
    rows = await database.fetch_all(
        """SELECT CASE_ID AS case_id, CASE_TYPE_CD AS case_type_cd,
                  TITLE_A_NM AS title_a_nm, TYPE_A_CD AS type_a_cd, SUB_A_NM AS sub_a_nm,
                  TITLE_B_NM AS title_b_nm, TYPE_B_CD AS type_b_cd, SUB_B_NM AS sub_b_nm,
                  POINTS_VAL AS points_val, VIEW_NO AS view_no, COMPARISON_NO AS comparison_no,
                  ACTIVE_YN AS active_yn, INS_DTM AS ins_dtm
           FROM TPOPULAR_CASE ORDER BY COMPARISON_NO DESC"""
    )
    for r in rows:
        if isinstance(r.get("points_val"), str):
            r["points_val"] = json.loads(r["points_val"])
        if r.get("ins_dtm"):
            r["ins_dtm"] = r["ins_dtm"].isoformat()
        r["active_yn"] = bool(r.get("active_yn"))
    return rows

@router.post("/popular-cases")
async def create_popular_case(req: PopularCaseReq, admin_id: int = Depends(get_admin_user)):
    points_json = json.dumps(req.points_val, ensure_ascii=False) if req.points_val else "[]"
    case_id = await database.execute(
        """INSERT INTO TPOPULAR_CASE
           (CASE_TYPE_CD, TITLE_A_NM, TYPE_A_CD, SUB_A_NM, TITLE_B_NM, TYPE_B_CD, SUB_B_NM, POINTS_VAL, ACTIVE_YN)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (req.case_type_cd, req.title_a_nm, req.type_a_cd, req.sub_a_nm,
         req.title_b_nm, req.type_b_cd, req.sub_b_nm, points_json, req.active_yn),
    )
    cache.delete("landing_popular")
    return {"case_id": case_id}

@router.put("/popular-cases/{case_id}")
async def update_popular_case(case_id: int, req: PopularCaseReq, admin_id: int = Depends(get_admin_user)):
    existing = await database.fetch_one("SELECT CASE_ID AS case_id FROM TPOPULAR_CASE WHERE CASE_ID=%s", (case_id,))
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Popular case not found")
    points_json = json.dumps(req.points_val, ensure_ascii=False) if req.points_val else "[]"
    await database.execute(
        """UPDATE TPOPULAR_CASE
           SET CASE_TYPE_CD=%s, TITLE_A_NM=%s, TYPE_A_CD=%s, SUB_A_NM=%s,
               TITLE_B_NM=%s, TYPE_B_CD=%s, SUB_B_NM=%s, POINTS_VAL=%s, ACTIVE_YN=%s
           WHERE CASE_ID=%s""",
        (req.case_type_cd, req.title_a_nm, req.type_a_cd, req.sub_a_nm,
         req.title_b_nm, req.type_b_cd, req.sub_b_nm, points_json, req.active_yn, case_id),
    )
    cache.delete("landing_popular")
    return {"ok": True}

@router.delete("/popular-cases/{case_id}")
async def delete_popular_case(case_id: int, admin_id: int = Depends(get_admin_user)):
    existing = await database.fetch_one("SELECT CASE_ID AS case_id FROM TPOPULAR_CASE WHERE CASE_ID=%s", (case_id,))
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Popular case not found")
    await database.execute("DELETE FROM TPOPULAR_CASE WHERE CASE_ID=%s", (case_id,))
    cache.delete("landing_popular")
    return {"ok": True}

# ━━ FEED ━━

@router.get("/feed", response_model=PagedResponse)
async def list_feed(
    page: int = Query(1, ge=1),
    admin_id: int = Depends(get_admin_user),
):
    page_size = 20
    offset = (page - 1) * page_size
    count_row = await database.fetch_one("SELECT COUNT(*) AS cnt FROM TCOMPARISON_FEED")
    rows = await database.fetch_all(
        """SELECT FEED_ID AS feed_id, COMPARISON_ID AS comparison_id, JOB_CTGR_NM AS job_ctgr_nm,
                  COMP_A_DISP_NM AS comp_a_disp_nm, COMP_A_TP_CD AS comp_a_tp_cd,
                  COMP_B_DISP_NM AS comp_b_disp_nm, COMP_B_TP_CD AS comp_b_tp_cd,
                  HEADLINE_CTNT AS headline_ctnt, DETAIL_CTNT AS detail_ctnt,
                  METRIC_VAL_CTNT AS metric_val_ctnt, METRIC_LABEL_NM AS metric_label_nm,
                  METRIC_TYPE_CD AS metric_type_cd, INS_DTM AS ins_dtm
           FROM TCOMPARISON_FEED ORDER BY INS_DTM DESC LIMIT %s OFFSET %s""",
        (page_size, offset),
    )
    for r in rows:
        if r.get("ins_dtm"):
            r["ins_dtm"] = r["ins_dtm"].isoformat()
    return PagedResponse(
        items=rows,
        total=int(count_row["cnt"]) if count_row else 0,
        page=page,
        page_size=page_size,
    )

@router.delete("/feed/{feed_id}")
async def delete_feed(feed_id: int, admin_id: int = Depends(get_admin_user)):
    existing = await database.fetch_one("SELECT FEED_ID AS feed_id FROM TCOMPARISON_FEED WHERE FEED_ID=%s", (feed_id,))
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feed not found")
    await database.execute("DELETE FROM TCOMPARISON_FEED WHERE FEED_ID=%s", (feed_id,))
    cache.delete("landing_feed")
    return {"ok": True}

# ━━ CACHE ━━

@router.post("/cache/clear")
async def clear_cache(admin_id: int = Depends(get_admin_user)):
    cache.clear()
    return {"ok": True}

# ━━ STATS ━━

@router.get("/stats/comparisons")
async def stats_comparisons(
    days: int = Query(30, ge=1, le=365),
    admin_id: int = Depends(get_admin_user),
):
    rows = await database.fetch_all(
        """SELECT STAT_DT AS stat_dt, COMPARISON_NO AS comparison_no
           FROM TDAILY_STAT
           WHERE STAT_DT >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
           ORDER BY STAT_DT""",
        (days,),
    )
    for r in rows:
        if r.get("stat_dt"):
            r["stat_dt"] = r["stat_dt"].isoformat() if hasattr(r["stat_dt"], "isoformat") else str(r["stat_dt"])
    return rows

@router.get("/stats/companies")
async def stats_popular_companies(admin_id: int = Depends(get_admin_user)):
    rows_a = await database.fetch_all(
        """SELECT COMP_A_NM AS comp_nm, COUNT(*) AS cnt
           FROM TCOMPARISON WHERE COMP_A_NM IS NOT NULL
           GROUP BY COMP_A_NM"""
    )
    rows_b = await database.fetch_all(
        """SELECT COMP_B_NM AS comp_nm, COUNT(*) AS cnt
           FROM TCOMPARISON WHERE COMP_B_NM IS NOT NULL
           GROUP BY COMP_B_NM"""
    )
    merged = {}
    for r in rows_a + rows_b:
        nm = r["comp_nm"]
        merged[nm] = merged.get(nm, 0) + int(r["cnt"])
    top10 = sorted(merged.items(), key=lambda x: x[1], reverse=True)[:10]
    return [{"comp_nm": nm, "comparison_no": cnt} for nm, cnt in top10]

@router.get("/stats/members")
async def stats_members(
    days: int = Query(30, ge=1, le=365),
    admin_id: int = Depends(get_admin_user),
):
    rows = await database.fetch_all(
        """SELECT DATE(INS_DTM) AS reg_dt, COUNT(*) AS cnt
           FROM TMEMBER
           WHERE INS_DTM >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
           GROUP BY DATE(INS_DTM)
           ORDER BY reg_dt""",
        (days,),
    )
    for r in rows:
        if r.get("reg_dt"):
            r["reg_dt"] = r["reg_dt"].isoformat() if hasattr(r["reg_dt"], "isoformat") else str(r["reg_dt"])
    return rows
