import json
import time
from fastapi import APIRouter, Depends, HTTPException, Query, status
import database
from services import cache
from middleware.auth_middleware import get_admin_user
from models.admin import (
    DashboardStats, CompanyCreate, CompanyUpdate,
    AliasUpdate, PopularCaseReq, UserRoleUpdate, PagedResponse,
)

router = APIRouter()

# ━━ DASHBOARD ━━

@router.get("/dashboard", response_model=DashboardStats)
async def dashboard(admin_id: int = Depends(get_admin_user)):
    total_users = await database.fetch_one("SELECT COUNT(*) AS cnt FROM users")
    today_users = await database.fetch_one(
        "SELECT COUNT(*) AS cnt FROM users WHERE DATE(created_at) = CURDATE()"
    )
    total_comparisons = await database.fetch_one("SELECT COUNT(*) AS cnt FROM comparisons")
    today_comparisons = await database.fetch_one(
        "SELECT comparison_count AS cnt FROM daily_stats WHERE stat_date = CURDATE()"
    )
    total_companies = await database.fetch_one("SELECT COUNT(*) AS cnt FROM companies")
    companies_with_ben = await database.fetch_one(
        "SELECT COUNT(DISTINCT company_id) AS cnt FROM company_benefits"
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
    if q:
        where = "WHERE email LIKE %s OR name LIKE %s"
        like = f"%{q}%"
        args = (like, like)
        count_row = await database.fetch_one(
            f"SELECT COUNT(*) AS cnt FROM users {where}", args
        )
        rows = await database.fetch_all(
            f"SELECT id, email, name, role, job_nm, created_at FROM users {where} ORDER BY created_at DESC LIMIT %s OFFSET %s",
            (*args, page_size, offset),
        )
    else:
        count_row = await database.fetch_one("SELECT COUNT(*) AS cnt FROM users")
        rows = await database.fetch_all(
            "SELECT id, email, name, role, job_nm, created_at FROM users ORDER BY created_at DESC LIMIT %s OFFSET %s",
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
    user = await database.fetch_one("SELECT id FROM users WHERE id=%s", (user_id,))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await database.execute("UPDATE users SET role=%s WHERE id=%s", (req.role, user_id))
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
        conditions.append("c.name LIKE %s")
        args.append(f"%{q}%")
    if type:
        conditions.append("c.type_id = %s")
        args.append(type)
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    count_row = await database.fetch_one(
        f"SELECT COUNT(*) AS cnt FROM companies c {where}", tuple(args)
    )
    rows = await database.fetch_all(
        f"""SELECT c.id, c.name, c.type_id AS type, c.industry,
                   COALESCE(b.ben_cnt, 0) AS benefit_count,
                   COALESCE(a.alias_cnt, 0) AS alias_count
            FROM companies c
            LEFT JOIN (SELECT company_id, COUNT(*) AS ben_cnt FROM company_benefits GROUP BY company_id) b ON b.company_id = c.id
            LEFT JOIN (SELECT company_id, COUNT(*) AS alias_cnt FROM company_aliases GROUP BY company_id) a ON a.company_id = c.id
            {where}
            ORDER BY c.name
            LIMIT %s OFFSET %s""",
        (*args, page_size, offset),
    )
    return PagedResponse(
        items=rows,
        total=int(count_row["cnt"]) if count_row else 0,
        page=page,
        page_size=page_size,
    )

@router.post("/companies")
async def create_company(req: CompanyCreate, admin_id: int = Depends(get_admin_user)):
    existing = await database.fetch_one("SELECT id FROM companies WHERE name=%s", (req.name,))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Company name already exists")
    # Generate id from name (lowercase, no spaces, max 30 chars)
    company_id = req.name.lower().replace(" ", "_")[:30]
    existing_id = await database.fetch_one("SELECT id FROM companies WHERE id=%s", (company_id,))
    if existing_id:
        import time as _t
        company_id = f"{company_id[:24]}_{int(_t.time()) % 100000}"
    work_style_json = json.dumps(req.work_style, ensure_ascii=False) if req.work_style else None
    await database.execute(
        """INSERT INTO companies (id, name, type_id, industry, logo, work_style, careers_benefit_url)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (company_id, req.name, req.type_id, req.industry, req.logo, work_style_json, req.careers_benefit_url),
    )
    cache.delete("reference_all")
    return {"id": company_id}

@router.put("/companies/{company_id}")
async def update_company(company_id: str, req: CompanyUpdate, admin_id: int = Depends(get_admin_user)):
    existing = await database.fetch_one("SELECT id FROM companies WHERE id=%s", (company_id,))
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    sets = []
    args = []
    if req.name is not None:
        sets.append("name=%s")
        args.append(req.name)
    if req.type_id is not None:
        sets.append("type_id=%s")
        args.append(req.type_id)
    if req.industry is not None:
        sets.append("industry=%s")
        args.append(req.industry)
    if req.logo is not None:
        sets.append("logo=%s")
        args.append(req.logo)
    if req.work_style is not None:
        sets.append("work_style=%s")
        args.append(json.dumps(req.work_style, ensure_ascii=False))
    if req.careers_benefit_url is not None:
        sets.append("careers_benefit_url=%s")
        args.append(req.careers_benefit_url)
    if not sets:
        return {"ok": True}
    args.append(company_id)
    await database.execute(
        f"UPDATE companies SET {', '.join(sets)} WHERE id=%s", tuple(args)
    )
    cache.delete("reference_all")
    return {"ok": True}

@router.delete("/companies/{company_id}")
async def delete_company(company_id: str, admin_id: int = Depends(get_admin_user)):
    existing = await database.fetch_one("SELECT id FROM companies WHERE id=%s", (company_id,))
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    await database.execute("DELETE FROM companies WHERE id=%s", (company_id,))
    cache.delete("reference_all")
    return {"ok": True}

# ━━ COMPANY BENEFITS ━━

@router.get("/companies/{company_id}/benefits")
async def get_company_benefits(company_id: str, admin_id: int = Depends(get_admin_user)):
    rows = await database.fetch_all(
        """SELECT id, ben_key, name, val, category, badge, note,
                  is_qualitative, qual_text, sort_order
           FROM company_benefits WHERE company_id=%s ORDER BY sort_order""",
        (company_id,),
    )
    return rows

@router.put("/companies/{company_id}/benefits")
async def save_company_benefits(
    company_id: str,
    benefits: list[dict],
    admin_id: int = Depends(get_admin_user),
):
    existing = await database.fetch_one("SELECT id FROM companies WHERE id=%s", (company_id,))
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    await database.execute("DELETE FROM company_benefits WHERE company_id=%s", (company_id,))
    for i, b in enumerate(benefits):
        await database.execute(
            """INSERT INTO company_benefits
               (company_id, ben_key, name, val, category, badge, note, is_qualitative, qual_text, sort_order)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (company_id, b.get("ben_key", ""), b.get("name", ""), b.get("val", 0),
             b.get("category", "financial"), b.get("badge", "est"), b.get("note"),
             b.get("is_qualitative", False), b.get("qual_text"), b.get("sort_order", i)),
        )
    cache.delete("reference_all")
    return {"ok": True, "count": len(benefits)}

# ━━ COMPANY ALIASES ━━

@router.put("/companies/{company_id}/aliases")
async def save_company_aliases(
    company_id: str,
    req: AliasUpdate,
    admin_id: int = Depends(get_admin_user),
):
    existing = await database.fetch_one("SELECT id FROM companies WHERE id=%s", (company_id,))
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    await database.execute("DELETE FROM company_aliases WHERE company_id=%s", (company_id,))
    for alias in req.aliases:
        if alias.strip():
            await database.execute(
                "INSERT INTO company_aliases (company_id, alias) VALUES (%s, %s)",
                (company_id, alias.strip()),
            )
    cache.delete("reference_all")
    return {"ok": True, "count": len(req.aliases)}

# ━━ POPULAR CASES ━━

@router.get("/popular-cases")
async def list_popular_cases(admin_id: int = Depends(get_admin_user)):
    rows = await database.fetch_all(
        """SELECT id, case_type, title_a, type_a, sub_a, title_b, type_b, sub_b,
                  points, view_count, comparison_count, is_active, created_at
           FROM popular_cases ORDER BY comparison_count DESC"""
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
        """INSERT INTO popular_cases
           (case_type, title_a, type_a, sub_a, title_b, type_b, sub_b, points, is_active)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (req.case_type, req.title_a, req.type_a, req.sub_a,
         req.title_b, req.type_b, req.sub_b, points_json, req.is_active),
    )
    cache.delete("landing_popular")
    return {"id": case_id}

@router.put("/popular-cases/{case_id}")
async def update_popular_case(case_id: int, req: PopularCaseReq, admin_id: int = Depends(get_admin_user)):
    existing = await database.fetch_one("SELECT id FROM popular_cases WHERE id=%s", (case_id,))
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Popular case not found")
    points_json = json.dumps(req.points, ensure_ascii=False) if req.points else "[]"
    await database.execute(
        """UPDATE popular_cases
           SET case_type=%s, title_a=%s, type_a=%s, sub_a=%s,
               title_b=%s, type_b=%s, sub_b=%s, points=%s, is_active=%s
           WHERE id=%s""",
        (req.case_type, req.title_a, req.type_a, req.sub_a,
         req.title_b, req.type_b, req.sub_b, points_json, req.is_active, case_id),
    )
    cache.delete("landing_popular")
    return {"ok": True}

@router.delete("/popular-cases/{case_id}")
async def delete_popular_case(case_id: int, admin_id: int = Depends(get_admin_user)):
    existing = await database.fetch_one("SELECT id FROM popular_cases WHERE id=%s", (case_id,))
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Popular case not found")
    await database.execute("DELETE FROM popular_cases WHERE id=%s", (case_id,))
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
    count_row = await database.fetch_one("SELECT COUNT(*) AS cnt FROM comparison_feed")
    rows = await database.fetch_all(
        """SELECT id, comparison_id, job_category, company_a_display, type_a,
                  company_b_display, type_b, headline, detail,
                  metric_val, metric_label, metric_type, created_at
           FROM comparison_feed ORDER BY created_at DESC LIMIT %s OFFSET %s""",
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
    existing = await database.fetch_one("SELECT id FROM comparison_feed WHERE id=%s", (feed_id,))
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feed not found")
    await database.execute("DELETE FROM comparison_feed WHERE id=%s", (feed_id,))
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
        """SELECT stat_date, comparison_count
           FROM daily_stats
           WHERE stat_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
           ORDER BY stat_date""",
        (days,),
    )
    for r in rows:
        if r.get("stat_date"):
            r["stat_date"] = r["stat_date"].isoformat() if hasattr(r["stat_date"], "isoformat") else str(r["stat_date"])
    return rows

@router.get("/stats/companies")
async def stats_popular_companies(admin_id: int = Depends(get_admin_user)):
    rows_a = await database.fetch_all(
        """SELECT company_a_name AS name, COUNT(*) AS cnt
           FROM comparisons WHERE company_a_name IS NOT NULL
           GROUP BY company_a_name"""
    )
    rows_b = await database.fetch_all(
        """SELECT company_b_name AS name, COUNT(*) AS cnt
           FROM comparisons WHERE company_b_name IS NOT NULL
           GROUP BY company_b_name"""
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
        """SELECT DATE(created_at) AS reg_date, COUNT(*) AS cnt
           FROM users
           WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
           GROUP BY DATE(created_at)
           ORDER BY reg_date""",
        (days,),
    )
    for r in rows:
        if r.get("reg_date"):
            r["reg_date"] = r["reg_date"].isoformat() if hasattr(r["reg_date"], "isoformat") else str(r["reg_date"])
    return rows
