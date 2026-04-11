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
    total_users = await database.fetch_one("SELECT COUNT(*) AS cnt FROM TMEMBER")
    today_users = await database.fetch_one(
        "SELECT COUNT(*) AS cnt FROM TMEMBER WHERE DATE(INS_DTM) = CURDATE()"
    )
    total_comparisons = await database.fetch_one("SELECT COUNT(*) AS cnt FROM TCOMPARISON")
    today_comparisons = await database.fetch_one(
        "SELECT COMPARISON_NO AS cnt FROM TDAILY_STAT WHERE STAT_DT = CURDATE()"
    )
    total_companies = await database.fetch_one("SELECT COUNT(*) AS cnt FROM TCOMPANY")
    companies_with_ben = await database.fetch_one(
        "SELECT COUNT(DISTINCT COMP_ID) AS cnt FROM TCOMPANY_BENEFIT"
    )
    # Active visitors from landing router
    from routers.landing import _get_active_count
    return DashboardStats(
        total_users=int(total_users["cnt"]) if total_users else 0,
        today_users=int(today_users["cnt"]) if today_users else 0,
        total_comparisons=int(total_comparisons["cnt"]) if total_comparisons else 0,
        today_comparisons=int(today_comparisons["cnt"]) if today_comparisons else 0,
        total_companies=int(total_companies["cnt"]) if total_companies else 0,
        companies_with_benefits=int(companies_with_ben["cnt"]) if companies_with_ben else 0,
        active_visitors=_get_active_count(),
    )

# ━━ USERS ━━

@router.get("/users", response_model=PagedResponse)
async def list_users(
    page: int = Query(1, ge=1),
    q: str = Query("", max_length=100),
    admin_id: int = Depends(get_admin_user),
):
    page_size = 20
    offset = (page - 1) * page_size
    select_cols = "MBR_ID AS id, EMAIL_ADDR AS email, MBR_NM AS name, ROLE_CD AS role, JOB_NM AS job_nm, INS_DTM AS created_at"
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
        if r.get("created_at"):
            r["created_at"] = r["created_at"].isoformat()
    return PagedResponse(
        items=rows,
        total=int(count_row["cnt"]) if count_row else 0,
        page=page,
        page_size=page_size,
    )

@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    req: UserRoleUpdate,
    admin_id: int = Depends(get_admin_user),
):
    if user_id == admin_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot change own role")
    user = await database.fetch_one("SELECT MBR_ID AS id FROM TMEMBER WHERE MBR_ID=%s", (user_id,))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await database.execute("UPDATE TMEMBER SET ROLE_CD=%s WHERE MBR_ID=%s", (req.role, user_id))
    return {"ok": True}

# ━━ COMPANIES ━━

@router.get("/companies", response_model=PagedResponse)
async def list_companies(
    page: int = Query(1, ge=1),
    q: str = Query("", max_length=100),
    type: str = Query("", max_length=20),
    admin_id: int = Depends(get_admin_user),
):
    page_size = 20
    offset = (page - 1) * page_size
    conditions = []
    args = []
    if q:
        conditions.append("c.COMP_NM LIKE %s")
        args.append(f"%{q}%")
    if type:
        conditions.append("ct.COMP_TP_CD = %s")
        args.append(type)
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    count_row = await database.fetch_one(
        f"SELECT COUNT(*) AS cnt FROM TCOMPANY c JOIN TCOMPANY_TYPE ct ON ct.COMP_TP_ID = c.COMP_TP_ID {where}",
        tuple(args),
    )
    rows = await database.fetch_all(
        f"""SELECT c.COMP_ID AS id, c.COMP_NM AS name, ct.COMP_TP_CD AS type, c.INDUSTRY_NM AS industry,
                   COALESCE(b.ben_cnt, 0) AS benefit_count,
                   COALESCE(a.alias_cnt, 0) AS alias_count
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

async def _resolve_comp_tp_id(type_cd: str) -> int | None:
    """COMP_TP_CD 문자열 코드를 INT PK로 변환."""
    row = await database.fetch_one(
        "SELECT COMP_TP_ID AS id FROM TCOMPANY_TYPE WHERE COMP_TP_CD=%s", (type_cd,)
    )
    return row["id"] if row else None


@router.post("/companies")
async def create_company(req: CompanyCreate, admin_id: int = Depends(get_admin_user)):
    existing = await database.fetch_one("SELECT COMP_ID AS id FROM TCOMPANY WHERE COMP_NM=%s", (req.name,))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Company name already exists")
    # COMP_ENG_NM 슬러그 생성 (기존 id 생성 로직 유지)
    eng_nm = req.name.lower().replace(" ", "_")[:30]
    existing_eng = await database.fetch_one("SELECT COMP_ID AS id FROM TCOMPANY WHERE COMP_ENG_NM=%s", (eng_nm,))
    if existing_eng:
        import time as _t
        eng_nm = f"{eng_nm[:24]}_{int(_t.time()) % 100000}"
    tp_id = await _resolve_comp_tp_id(req.type_id)
    if not tp_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown company type")
    work_style_json = json.dumps(req.work_style, ensure_ascii=False) if req.work_style else None
    new_id = await database.execute(
        """INSERT INTO TCOMPANY (COMP_ENG_NM, COMP_NM, COMP_TP_ID, INDUSTRY_NM, LOGO_NM, WORK_STYLE_VAL, CAREERS_BENEFIT_URL)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (eng_nm, req.name, tp_id, req.industry, req.logo, work_style_json, req.careers_benefit_url),
    )
    cache.delete("reference_all")
    return {"id": new_id}

@router.put("/companies/{company_id}")
async def update_company(company_id: int, req: CompanyUpdate, admin_id: int = Depends(get_admin_user)):
    existing = await database.fetch_one("SELECT COMP_ID AS id FROM TCOMPANY WHERE COMP_ID=%s", (company_id,))
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    sets = []
    args = []
    if req.name is not None:
        sets.append("COMP_NM=%s")
        args.append(req.name)
    if req.type_id is not None:
        tp_id = await _resolve_comp_tp_id(req.type_id)
        if not tp_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown company type")
        sets.append("COMP_TP_ID=%s")
        args.append(tp_id)
    if req.industry is not None:
        sets.append("INDUSTRY_NM=%s")
        args.append(req.industry)
    if req.logo is not None:
        sets.append("LOGO_NM=%s")
        args.append(req.logo)
    if req.work_style is not None:
        sets.append("WORK_STYLE_VAL=%s")
        args.append(json.dumps(req.work_style, ensure_ascii=False))
    if req.careers_benefit_url is not None:
        sets.append("CAREERS_BENEFIT_URL=%s")
        args.append(req.careers_benefit_url)
    if not sets:
        return {"ok": True}
    args.append(company_id)
    await database.execute(
        f"UPDATE TCOMPANY SET {', '.join(sets)} WHERE COMP_ID=%s", tuple(args)
    )
    cache.delete("reference_all")
    return {"ok": True}

@router.delete("/companies/{company_id}")
async def delete_company(company_id: int, admin_id: int = Depends(get_admin_user)):
    existing = await database.fetch_one("SELECT COMP_ID AS id FROM TCOMPANY WHERE COMP_ID=%s", (company_id,))
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    await database.execute("DELETE FROM TCOMPANY WHERE COMP_ID=%s", (company_id,))
    cache.delete("reference_all")
    return {"ok": True}

# ━━ COMPANY BENEFITS ━━

@router.get("/companies/{company_id}/benefits")
async def get_company_benefits(company_id: int, admin_id: int = Depends(get_admin_user)):
    rows = await database.fetch_all(
        """SELECT BENEFIT_ID AS id, BENEFIT_CD AS ben_key, BENEFIT_NM AS name, BENEFIT_AMT AS val,
                  BENEFIT_CTGR_CD AS category, BADGE_CD AS badge, NOTE_CTNT AS note,
                  QUAL_YN AS is_qualitative, QUAL_DESC_CTNT AS qual_text, SORT_ORDER_NO AS sort_order
           FROM TCOMPANY_BENEFIT WHERE COMP_ID=%s ORDER BY SORT_ORDER_NO""",
        (company_id,),
    )
    return rows

@router.put("/companies/{company_id}/benefits")
async def save_company_benefits(
    company_id: int,
    benefits: list[BenefitItem],
    admin_id: int = Depends(get_admin_user),
):
    existing = await database.fetch_one("SELECT COMP_ID AS id FROM TCOMPANY WHERE COMP_ID=%s", (company_id,))
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    await database.execute("DELETE FROM TCOMPANY_BENEFIT WHERE COMP_ID=%s", (company_id,))
    for i, b in enumerate(benefits):
        await database.execute(
            """INSERT INTO TCOMPANY_BENEFIT
               (COMP_ID, BENEFIT_CD, BENEFIT_NM, BENEFIT_AMT, BENEFIT_CTGR_CD, BADGE_CD, NOTE_CTNT, QUAL_YN, QUAL_DESC_CTNT, SORT_ORDER_NO)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (company_id, b.ben_key, b.name, b.val,
             b.category, b.badge, b.note,
             b.is_qualitative, b.qual_text, b.sort_order or i),
        )
    cache.delete("reference_all")
    return {"ok": True, "count": len(benefits)}

# ━━ COMPANY ALIASES ━━

@router.put("/companies/{company_id}/aliases")
async def save_company_aliases(
    company_id: int,
    req: AliasUpdate,
    admin_id: int = Depends(get_admin_user),
):
    existing = await database.fetch_one("SELECT COMP_ID AS id FROM TCOMPANY WHERE COMP_ID=%s", (company_id,))
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    await database.execute("DELETE FROM TCOMPANY_ALIAS WHERE COMP_ID=%s", (company_id,))
    for alias in req.aliases:
        if alias.strip():
            await database.execute(
                "INSERT INTO TCOMPANY_ALIAS (COMP_ID, ALIAS_NM) VALUES (%s, %s)",
                (company_id, alias.strip()),
            )
    cache.delete("reference_all")
    return {"ok": True, "count": len(req.aliases)}

# ━━ POPULAR CASES ━━

@router.get("/popular-cases")
async def list_popular_cases(admin_id: int = Depends(get_admin_user)):
    rows = await database.fetch_all(
        """SELECT CASE_ID AS id, CASE_TYPE_CD AS case_type, TITLE_A_NM AS title_a, TYPE_A_CD AS type_a,
                  SUB_A_NM AS sub_a, TITLE_B_NM AS title_b, TYPE_B_CD AS type_b, SUB_B_NM AS sub_b,
                  POINTS_VAL AS points, VIEW_NO AS view_count, COMPARISON_NO AS comparison_count,
                  ACTIVE_YN AS is_active, INS_DTM AS created_at
           FROM TPOPULAR_CASE ORDER BY COMPARISON_NO DESC"""
    )
    for r in rows:
        if isinstance(r.get("points"), str):
            r["points"] = json.loads(r["points"])
        if r.get("created_at"):
            r["created_at"] = r["created_at"].isoformat()
        r["is_active"] = bool(r.get("is_active"))
    return rows

@router.post("/popular-cases")
async def create_popular_case(req: PopularCaseReq, admin_id: int = Depends(get_admin_user)):
    points_json = json.dumps(req.points, ensure_ascii=False) if req.points else "[]"
    case_id = await database.execute(
        """INSERT INTO TPOPULAR_CASE
           (CASE_TYPE_CD, TITLE_A_NM, TYPE_A_CD, SUB_A_NM, TITLE_B_NM, TYPE_B_CD, SUB_B_NM, POINTS_VAL, ACTIVE_YN)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (req.case_type, req.title_a, req.type_a, req.sub_a,
         req.title_b, req.type_b, req.sub_b, points_json, req.is_active),
    )
    cache.delete("landing_popular")
    return {"id": case_id}

@router.put("/popular-cases/{case_id}")
async def update_popular_case(case_id: int, req: PopularCaseReq, admin_id: int = Depends(get_admin_user)):
    existing = await database.fetch_one("SELECT CASE_ID AS id FROM TPOPULAR_CASE WHERE CASE_ID=%s", (case_id,))
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Popular case not found")
    points_json = json.dumps(req.points, ensure_ascii=False) if req.points else "[]"
    await database.execute(
        """UPDATE TPOPULAR_CASE
           SET CASE_TYPE_CD=%s, TITLE_A_NM=%s, TYPE_A_CD=%s, SUB_A_NM=%s,
               TITLE_B_NM=%s, TYPE_B_CD=%s, SUB_B_NM=%s, POINTS_VAL=%s, ACTIVE_YN=%s
           WHERE CASE_ID=%s""",
        (req.case_type, req.title_a, req.type_a, req.sub_a,
         req.title_b, req.type_b, req.sub_b, points_json, req.is_active, case_id),
    )
    cache.delete("landing_popular")
    return {"ok": True}

@router.delete("/popular-cases/{case_id}")
async def delete_popular_case(case_id: int, admin_id: int = Depends(get_admin_user)):
    existing = await database.fetch_one("SELECT CASE_ID AS id FROM TPOPULAR_CASE WHERE CASE_ID=%s", (case_id,))
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
        """SELECT FEED_ID AS id, COMPARISON_ID AS comparison_id, JOB_CTGR_NM AS job_category,
                  COMP_A_DISP_NM AS company_a_display, COMP_A_TP_CD AS type_a,
                  COMP_B_DISP_NM AS company_b_display, COMP_B_TP_CD AS type_b,
                  HEADLINE_CTNT AS headline, DETAIL_CTNT AS detail,
                  METRIC_VAL_CTNT AS metric_val, METRIC_LABEL_NM AS metric_label,
                  METRIC_TYPE_CD AS metric_type, INS_DTM AS created_at
           FROM TCOMPARISON_FEED ORDER BY INS_DTM DESC LIMIT %s OFFSET %s""",
        (page_size, offset),
    )
    for r in rows:
        if r.get("created_at"):
            r["created_at"] = r["created_at"].isoformat()
    return PagedResponse(
        items=rows,
        total=int(count_row["cnt"]) if count_row else 0,
        page=page,
        page_size=page_size,
    )

@router.delete("/feed/{feed_id}")
async def delete_feed(feed_id: int, admin_id: int = Depends(get_admin_user)):
    existing = await database.fetch_one("SELECT FEED_ID AS id FROM TCOMPARISON_FEED WHERE FEED_ID=%s", (feed_id,))
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
        """SELECT STAT_DT AS stat_date, COMPARISON_NO AS comparison_count
           FROM TDAILY_STAT
           WHERE STAT_DT >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
           ORDER BY STAT_DT""",
        (days,),
    )
    for r in rows:
        if r.get("stat_date"):
            r["stat_date"] = r["stat_date"].isoformat() if hasattr(r["stat_date"], "isoformat") else str(r["stat_date"])
    return rows

@router.get("/stats/companies")
async def stats_popular_companies(admin_id: int = Depends(get_admin_user)):
    rows_a = await database.fetch_all(
        """SELECT COMP_A_NM AS name, COUNT(*) AS cnt
           FROM TCOMPARISON WHERE COMP_A_NM IS NOT NULL
           GROUP BY COMP_A_NM"""
    )
    rows_b = await database.fetch_all(
        """SELECT COMP_B_NM AS name, COUNT(*) AS cnt
           FROM TCOMPARISON WHERE COMP_B_NM IS NOT NULL
           GROUP BY COMP_B_NM"""
    )
    merged = {}
    for r in rows_a + rows_b:
        name = r["name"]
        merged[name] = merged.get(name, 0) + int(r["cnt"])
    top10 = sorted(merged.items(), key=lambda x: x[1], reverse=True)[:10]
    return [{"name": name, "count": cnt} for name, cnt in top10]

@router.get("/stats/users")
async def stats_users(
    days: int = Query(30, ge=1, le=365),
    admin_id: int = Depends(get_admin_user),
):
    rows = await database.fetch_all(
        """SELECT DATE(INS_DTM) AS reg_date, COUNT(*) AS cnt
           FROM TMEMBER
           WHERE INS_DTM >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
           GROUP BY DATE(INS_DTM)
           ORDER BY reg_date""",
        (days,),
    )
    for r in rows:
        if r.get("reg_date"):
            r["reg_date"] = r["reg_date"].isoformat() if hasattr(r["reg_date"], "isoformat") else str(r["reg_date"])
    return rows
