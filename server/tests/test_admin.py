"""
Admin API test suite for Job Choice OS.
Run: cd server && python -m pytest tests/test_admin.py -v
  or: cd server && python tests/test_admin.py

Strategy: Mock database.fetch_one / fetch_all / execute at module level
so no real DB connection is needed. Tests focus on auth gates, request
routing, and response shapes.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import AsyncMock, patch, MagicMock
from services.auth_service import create_token


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _admin_token(mbr_id: int = 1) -> dict:
    """Return Authorization header with admin JWT."""
    token = create_token(mbr_id, role_cd="admin")
    return {"Authorization": f"Bearer {token}"}

def _user_token(mbr_id: int = 2) -> dict:
    """Return Authorization header with regular user JWT."""
    token = create_token(mbr_id, role_cd="user")
    return {"Authorization": f"Bearer {token}"}

def _client():
    """Create a TestClient with server exceptions suppressed."""
    from fastapi.testclient import TestClient
    import main
    return TestClient(main.app, raise_server_exceptions=False)


# ━━ AUTH / PERMISSION GATES ━━

def test_admin_endpoints_require_token():
    """All /admin/* endpoints return 401/403 without a token."""
    c = _client()
    endpoints = [
        ("GET",  "/api/v1/admin/dashboard"),
        ("GET",  "/api/v1/admin/members"),
        ("PUT",  "/api/v1/admin/members/1/role"),
        ("GET",  "/api/v1/admin/companies"),
        ("POST", "/api/v1/admin/companies"),
        ("PUT",  "/api/v1/admin/companies/1"),
        ("DELETE", "/api/v1/admin/companies/1"),
        ("PUT",  "/api/v1/admin/companies/1/benefits"),
        ("PUT",  "/api/v1/admin/companies/1/aliases"),
        ("GET",  "/api/v1/admin/popular-cases"),
        ("POST", "/api/v1/admin/popular-cases"),
        ("PUT",  "/api/v1/admin/popular-cases/1"),
        ("DELETE", "/api/v1/admin/popular-cases/1"),
        ("GET",  "/api/v1/admin/stats/comparisons"),
        ("GET",  "/api/v1/admin/stats/companies"),
        ("GET",  "/api/v1/admin/stats/members"),
        ("POST", "/api/v1/admin/cache/clear"),
    ]
    for method, path in endpoints:
        r = getattr(c, method.lower())(path)
        assert r.status_code == 403, f"{method} {path} should be 403 without token, got {r.status_code}"


def test_admin_endpoints_reject_regular_user():
    """Regular user token gets 403 on admin endpoints."""
    c = _client()
    h = _user_token()
    r = c.get("/api/v1/admin/dashboard", headers=h)
    assert r.status_code == 403

    r = c.get("/api/v1/admin/members", headers=h)
    assert r.status_code == 403

    r = c.post("/api/v1/admin/cache/clear", headers=h)
    assert r.status_code == 403


def test_admin_endpoints_reject_invalid_token():
    """Garbage token gets 401/403."""
    c = _client()
    h = {"Authorization": "Bearer garbage.token.here"}
    r = c.get("/api/v1/admin/dashboard", headers=h)
    assert r.status_code in (401, 403)


# ━━ DASHBOARD ━━

@patch("database.fetch_one", new_callable=AsyncMock)
def test_dashboard_returns_stats(mock_fetch):
    mock_fetch.side_effect = [
        {"cnt": 100},   # total_users
        {"cnt": 5},     # today_users
        {"cnt": 500},   # total_comparisons
        {"cnt": 10},    # today_comparisons
        {"cnt": 50},    # total_companies
        {"cnt": 30},    # companies_with_benefits
    ]
    c = _client()
    r = c.get("/api/v1/admin/dashboard", headers=_admin_token())
    assert r.status_code == 200
    data = r.json()
    assert data["total_mbr_no"] == 100
    assert data["today_mbr_no"] == 5
    assert data["total_comparison_no"] == 500
    assert data["total_comp_no"] == 50
    assert "active_visitor_no" in data


# ━━ USERS ━━

@patch("database.fetch_all", new_callable=AsyncMock, return_value=[
    {"mbr_id": 1, "email_addr": "admin@test.com", "mbr_nm": "Admin", "role_cd": "admin", "job_nm": "Dev", "ins_dtm": None},
    {"mbr_id": 2, "email_addr": "user@test.com", "mbr_nm": "User", "role_cd": "user", "job_nm": "PM", "ins_dtm": None},
])
@patch("database.fetch_one", new_callable=AsyncMock, return_value={"cnt": 2})
def test_list_users(mock_one, mock_all):
    c = _client()
    r = c.get("/api/v1/admin/members", headers=_admin_token())
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["page"] == 1


@patch("database.fetch_all", new_callable=AsyncMock, return_value=[
    {"mbr_id": 2, "email_addr": "user@test.com", "mbr_nm": "User", "role_cd": "user", "job_nm": "PM", "ins_dtm": None},
])
@patch("database.fetch_one", new_callable=AsyncMock, return_value={"cnt": 1})
def test_list_users_with_search(mock_one, mock_all):
    c = _client()
    r = c.get("/api/v1/admin/members?q=user", headers=_admin_token())
    assert r.status_code == 200
    assert r.json()["total"] == 1


@patch("database.execute", new_callable=AsyncMock, return_value=None)
@patch("database.fetch_one", new_callable=AsyncMock, return_value={"id": 2})
def test_update_user_role_success(mock_one, mock_exec):
    c = _client()
    r = c.put(
        "/api/v1/admin/members/2/role",
        json={"role_cd": "admin"},
        headers=_admin_token(mbr_id=1),
    )
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_update_own_role_forbidden():
    """Admin cannot change their own role."""
    c = _client()
    # admin_id=1 trying to change user_id=1
    r = c.put(
        "/api/v1/admin/members/1/role",
        json={"role_cd": "user"},
        headers=_admin_token(mbr_id=1),
    )
    assert r.status_code == 403
    assert "own role" in r.json()["detail"].lower()


@patch("database.fetch_one", new_callable=AsyncMock, return_value=None)
def test_update_role_user_not_found(mock_one):
    c = _client()
    r = c.put(
        "/api/v1/admin/members/999/role",
        json={"role_cd": "admin"},
        headers=_admin_token(mbr_id=1),
    )
    assert r.status_code == 404


# ━━ COMPANIES ━━

@patch("database.fetch_all", new_callable=AsyncMock, return_value=[
    {"comp_id": 1, "comp_nm": "Samsung", "comp_tp_cd": "large", "industry_nm": "IT", "benefit_no": 10, "alias_no": 2},
])
@patch("database.fetch_one", new_callable=AsyncMock, return_value={"cnt": 1})
def test_list_companies(mock_one, mock_all):
    c = _client()
    r = c.get("/api/v1/admin/companies", headers=_admin_token())
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["comp_id"] == 1


@patch("database.fetch_all", new_callable=AsyncMock, return_value=[])
@patch("database.fetch_one", new_callable=AsyncMock, return_value={"cnt": 0})
def test_list_companies_with_filters(mock_one, mock_all):
    c = _client()
    r = c.get("/api/v1/admin/companies?q=test&type=startup", headers=_admin_token())
    assert r.status_code == 200
    assert r.json()["total"] == 0


@patch("database.execute", new_callable=AsyncMock, return_value=1)
@patch("database.fetch_one", new_callable=AsyncMock, side_effect=[None, None, {"comp_tp_id": 7}])  # name check, eng_nm check, type_cd lookup
def test_create_company(mock_one, mock_exec):
    c = _client()
    r = c.post(
        "/api/v1/admin/companies",
        json={"comp_nm": "TestCorp", "comp_tp_cd": "startup"},
        headers=_admin_token(),
    )
    assert r.status_code == 200
    assert "case_id" in r.json() or "comp_id" in r.json() or "ok" in r.json()


@patch("database.fetch_one", new_callable=AsyncMock, return_value={"id": 42})
def test_create_company_duplicate_name(mock_one):
    c = _client()
    r = c.post(
        "/api/v1/admin/companies",
        json={"comp_nm": "Existing", "comp_tp_cd": "large"},
        headers=_admin_token(),
    )
    assert r.status_code == 409


@patch("database.execute", new_callable=AsyncMock, return_value=None)
@patch("database.fetch_one", new_callable=AsyncMock, return_value={"id": 1})
def test_update_company(mock_one, mock_exec):
    c = _client()
    r = c.put(
        "/api/v1/admin/companies/1",
        json={"comp_nm": "Samsung Electronics", "industry_nm": "Semiconductor"},
        headers=_admin_token(),
    )
    assert r.status_code == 200
    assert r.json()["ok"] is True


@patch("database.fetch_one", new_callable=AsyncMock, return_value=None)
def test_update_company_not_found(mock_one):
    c = _client()
    r = c.put(
        "/api/v1/admin/companies/999",
        json={"comp_nm": "Nope"},
        headers=_admin_token(),
    )
    assert r.status_code == 404


@patch("database.execute", new_callable=AsyncMock, return_value=None)
@patch("database.fetch_one", new_callable=AsyncMock, return_value={"id": 1})
def test_delete_company(mock_one, mock_exec):
    c = _client()
    r = c.delete("/api/v1/admin/companies/1", headers=_admin_token())
    assert r.status_code == 200
    assert r.json()["ok"] is True


@patch("database.fetch_one", new_callable=AsyncMock, return_value=None)
def test_delete_company_not_found(mock_one):
    c = _client()
    r = c.delete("/api/v1/admin/companies/999", headers=_admin_token())
    assert r.status_code == 404


# ━━ COMPANY BENEFITS ━━

@patch("database.execute", new_callable=AsyncMock, return_value=None)
@patch("database.fetch_one", new_callable=AsyncMock, return_value={"id": 1})
def test_save_company_benefits(mock_one, mock_exec):
    c = _client()
    benefits = [
        {"benefit_cd": "meal", "benefit_nm": "Meal", "benefit_amt": 150, "benefit_ctgr_cd": "work_env"},
        {"benefit_cd": "bonus", "benefit_nm": "Bonus", "benefit_amt": 300, "benefit_ctgr_cd": "compensation"},
    ]
    r = c.put(
        "/api/v1/admin/companies/1/benefits",
        json=benefits,
        headers=_admin_token(),
    )
    assert r.status_code == 200
    assert r.json()["count"] == 2


@patch("database.fetch_one", new_callable=AsyncMock, return_value=None)
def test_save_benefits_company_not_found(mock_one):
    c = _client()
    r = c.put(
        "/api/v1/admin/companies/999/benefits",
        json=[{"benefit_cd": "meal", "benefit_nm": "Meal", "benefit_amt": 100}],
        headers=_admin_token(),
    )
    assert r.status_code == 404


@patch("database.fetch_all", new_callable=AsyncMock, return_value=[
    {"id": 1, "benefit_cd": "meal", "name": "Meal", "benefit_amt": 150.0, "benefit_ctgr_cd": "work_env",
     "badge": "est", "note": None, "is_qualitative": 0, "qual_text": None, "sort_order": 0},
])
def test_get_company_benefits(mock_all):
    c = _client()
    r = c.get("/api/v1/admin/companies/1/benefits", headers=_admin_token())
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["benefit_cd"] == "meal"


# ━━ COMPANY ALIASES ━━

@patch("database.execute", new_callable=AsyncMock, return_value=None)
@patch("database.fetch_one", new_callable=AsyncMock, return_value={"id": 1})
def test_save_company_aliases(mock_one, mock_exec):
    c = _client()
    r = c.put(
        "/api/v1/admin/companies/1/aliases",
        json={"aliases": ["Samsung Electronics", "SEC"]},
        headers=_admin_token(),
    )
    assert r.status_code == 200
    assert r.json()["count"] == 2


@patch("database.fetch_one", new_callable=AsyncMock, return_value=None)
def test_save_aliases_company_not_found(mock_one):
    c = _client()
    r = c.put(
        "/api/v1/admin/companies/999/aliases",
        json={"aliases": ["Test"]},
        headers=_admin_token(),
    )
    assert r.status_code == 404


# ━━ POPULAR CASES ━━

@patch("database.fetch_all", new_callable=AsyncMock, return_value=[
    {"case_id": 1, "case_type_cd": "company", "title_a_nm": "Samsung", "type_a_cd": "large",
     "sub_a_nm": None, "title_b_nm": "Toss", "type_b_cd": "startup", "sub_b_nm": None,
     "points_val": '["point1"]', "view_no": 100, "comparison_no": 50,
     "active_yn": 1, "created_at": None},
])
def test_list_popular_cases(mock_all):
    c = _client()
    r = c.get("/api/v1/admin/popular-cases", headers=_admin_token())
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["title_a_nm"] == "Samsung"
    assert data[0]["points_val"] == ["point1"]
    assert data[0]["active_yn"] is True


@patch("database.execute", new_callable=AsyncMock, return_value=1)
def test_create_popular_case(mock_exec):
    c = _client()
    r = c.post(
        "/api/v1/admin/popular-cases",
        json={
            "case_type_cd": "company",
            "title_a_nm": "Samsung",
            "type_a_cd": "large",
            "title_b_nm": "Toss",
            "type_b_cd": "startup",
            "points_val": ["Higher salary", "Better WLB"],
        },
        headers=_admin_token(),
    )
    assert r.status_code == 200
    assert "case_id" in r.json() or "comp_id" in r.json() or "ok" in r.json()


@patch("database.execute", new_callable=AsyncMock, return_value=None)
@patch("database.fetch_one", new_callable=AsyncMock, return_value={"id": 1})
def test_update_popular_case(mock_one, mock_exec):
    c = _client()
    r = c.put(
        "/api/v1/admin/popular-cases/1",
        json={
            "case_type_cd": "type",
            "title_a_nm": "Large Corp",
            "type_a_cd": "large",
            "title_b_nm": "Startup",
            "type_b_cd": "startup",
        },
        headers=_admin_token(),
    )
    assert r.status_code == 200
    assert r.json()["ok"] is True


@patch("database.fetch_one", new_callable=AsyncMock, return_value=None)
def test_update_popular_case_not_found(mock_one):
    c = _client()
    r = c.put(
        "/api/v1/admin/popular-cases/999",
        json={
            "case_type_cd": "company",
            "title_a_nm": "A", "type_a_cd": "large",
            "title_b_nm": "B", "type_b_cd": "startup",
        },
        headers=_admin_token(),
    )
    assert r.status_code == 404


@patch("database.execute", new_callable=AsyncMock, return_value=None)
@patch("database.fetch_one", new_callable=AsyncMock, return_value={"id": 1})
def test_delete_popular_case(mock_one, mock_exec):
    c = _client()
    r = c.delete("/api/v1/admin/popular-cases/1", headers=_admin_token())
    assert r.status_code == 200
    assert r.json()["ok"] is True


@patch("database.fetch_one", new_callable=AsyncMock, return_value=None)
def test_delete_popular_case_not_found(mock_one):
    c = _client()
    r = c.delete("/api/v1/admin/popular-cases/999", headers=_admin_token())
    assert r.status_code == 404


# ━━ STATS ━━

@patch("database.fetch_all", new_callable=AsyncMock, return_value=[
    {"stat_date": "2026-04-01", "comparison_no": 15},
    {"stat_date": "2026-04-02", "comparison_no": 20},
])
def test_stats_comparisons(mock_all):
    c = _client()
    r = c.get("/api/v1/admin/stats/comparisons", headers=_admin_token())
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2


@patch("database.fetch_all", new_callable=AsyncMock, return_value=[
    {"stat_date": "2026-04-01", "comparison_no": 15},
])
def test_stats_comparisons_custom_days(mock_all):
    c = _client()
    r = c.get("/api/v1/admin/stats/comparisons?days=7", headers=_admin_token())
    assert r.status_code == 200


@patch("database.fetch_all", new_callable=AsyncMock, side_effect=[
    [{"comp_nm": "Samsung", "cnt": 10}, {"comp_nm": "Toss", "cnt": 5}],  # rows_a
    [{"comp_nm": "Samsung", "cnt": 3}, {"comp_nm": "Kakao", "cnt": 7}],  # rows_b
])
def test_stats_companies(mock_all):
    c = _client()
    r = c.get("/api/v1/admin/stats/companies", headers=_admin_token())
    assert r.status_code == 200
    data = r.json()
    # Samsung: 10+3=13, Kakao: 7, Toss: 5
    names = [item["comp_nm"] for item in data]
    assert "Samsung" in names
    assert data[0]["comparison_no"] == 13  # Samsung is top


@patch("database.fetch_all", new_callable=AsyncMock, return_value=[
    {"reg_date": "2026-04-01", "cnt": 3},
    {"reg_date": "2026-04-02", "cnt": 5},
])
def test_stats_users(mock_all):
    c = _client()
    r = c.get("/api/v1/admin/stats/members", headers=_admin_token())
    assert r.status_code == 200
    assert len(r.json()) == 2


# ━━ CACHE ━━

def test_cache_clear():
    c = _client()
    r = c.post("/api/v1/admin/cache/clear", headers=_admin_token())
    assert r.status_code == 200
    assert r.json()["ok"] is True


# ━━ FEED ━━

@patch("database.fetch_all", new_callable=AsyncMock, return_value=[
    {"id": 1, "comparison_id": 10, "job_category": "dev", "company_a_display": "A",
     "type_a_cd": "large", "company_b_display": "B", "type_b_cd": "startup",
     "headline": "Test", "detail": None, "metric_val": "15%",
     "metric_label": "salary", "metric_type": "pos", "created_at": None},
])
@patch("database.fetch_one", new_callable=AsyncMock, return_value={"cnt": 1})
def test_list_feed(mock_one, mock_all):
    c = _client()
    r = c.get("/api/v1/admin/feed", headers=_admin_token())
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1


@patch("database.execute", new_callable=AsyncMock, return_value=None)
@patch("database.fetch_one", new_callable=AsyncMock, return_value={"id": 1})
def test_delete_feed(mock_one, mock_exec):
    c = _client()
    r = c.delete("/api/v1/admin/feed/1", headers=_admin_token())
    assert r.status_code == 200
    assert r.json()["ok"] is True


@patch("database.fetch_one", new_callable=AsyncMock, return_value=None)
def test_delete_feed_not_found(mock_one):
    c = _client()
    r = c.delete("/api/v1/admin/feed/999", headers=_admin_token())
    assert r.status_code == 404


# ━━ VALIDATION ━━

def test_create_company_missing_required_fields():
    """POST /admin/companies without required fields returns 422."""
    c = _client()
    r = c.post(
        "/api/v1/admin/companies",
        json={"comp_nm": "OnlyName"},  # missing type_id
        headers=_admin_token(),
    )
    assert r.status_code == 422


def test_update_role_missing_body():
    """PUT /admin/users/{id}/role without body returns 422."""
    c = _client()
    r = c.put("/api/v1/admin/members/2/role", headers=_admin_token(mbr_id=1))
    assert r.status_code == 422


def test_save_aliases_invalid_body():
    """PUT /admin/companies/{id}/aliases with wrong body returns 422."""
    c = _client()
    r = c.put(
        "/api/v1/admin/companies/test/aliases",
        json={"wrong_key": ["a"]},
        headers=_admin_token(),
    )
    assert r.status_code == 422


def test_update_role_invalid_value():
    """PUT /admin/users/{id}/role with invalid role value returns 422."""
    c = _client()
    r = c.put(
        "/api/v1/admin/members/2/role",
        json={"role_cd": "superadmin"},
        headers=_admin_token(mbr_id=1),
    )
    assert r.status_code == 422


def test_popular_case_missing_required():
    """POST /admin/popular-cases missing required fields returns 422."""
    c = _client()
    r = c.post(
        "/api/v1/admin/popular-cases",
        json={"case_type_cd": "company"},  # missing title_a, type_a, title_b, type_b
        headers=_admin_token(),
    )
    assert r.status_code == 422


# ━━ FRONTEND PATH VALIDATION ━━

def test_no_double_api_prefix_in_frontend():
    """apiFetch() 호출에 /api/v1/ prefix가 포함되면 이중 prefix 버그.
    apiFetch()가 자동으로 /api/v1을 붙이므로 경로에 /api/v1/을 넣으면
    실제 요청이 /api/v1/api/v1/... 로 가서 404 발생."""
    import re, os
    html_path = os.path.join(os.path.dirname(__file__), "..", "..", "index.html")
    with open(html_path) as f:
        content = f.read()
    matches = re.findall(r"apiFetch\s*\(\s*['\"]\/api\/v1\/", content)
    assert len(matches) == 0, f"이중 prefix 버그 {len(matches)}건: {matches}"


# ━━ RUNNER ━━

if __name__ == "__main__":
    import traceback
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"  \u2713 {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  \u2717 {t.__name__}: {e}")
            traceback.print_exc()
            failed += 1
    print(f"\n{'━' * 40}")
    print(f"  {passed} passed, {failed} failed, {passed + failed} total")
    if failed:
        sys.exit(1)
