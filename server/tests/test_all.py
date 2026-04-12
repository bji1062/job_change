"""
Comprehensive test suite for Job Choice OS backend.
Run: cd server && python -m pytest tests/test_all.py -v
  or: cd server && python tests/test_all.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decimal import Decimal


# ━━ AUTH SERVICE ━━

def test_hash_and_verify_password():
    from services.auth_service import hash_password, verify_password
    h = hash_password("test123")
    assert verify_password("test123", h)
    assert not verify_password("wrong", h)


def test_jwt_create_and_decode():
    from services.auth_service import create_token, decode_token
    token = create_token(42)
    assert decode_token(token) == 42


def test_jwt_invalid_token():
    from services.auth_service import decode_token
    assert decode_token("garbage") is None
    assert decode_token("") is None


# ━━ CACHE ━━

def test_cache_set_get():
    from services.cache import get, set, delete
    set("test_key", {"hello": "world"}, ttl=10)
    assert get("test_key") == {"hello": "world"}
    delete("test_key")


def test_cache_delete():
    from services.cache import get, set, delete
    set("del_test", "data")
    delete("del_test")
    assert get("del_test") is None


def test_cache_clear():
    from services.cache import get, set, clear
    set("k1", "v1"); set("k2", "v2")
    clear()
    assert get("k1") is None and get("k2") is None


def test_cache_ttl_expiration():
    from services.cache import get, set
    set("ttl_test", "data", ttl=0)
    assert get("ttl_test") is None


# ━━ DATABASE HELPERS ━━

def test_convert_row_none():
    from database import _convert_row
    assert _convert_row(None) is None


def test_convert_row_decimal():
    from database import _convert_row
    row = {"salary": Decimal("5000.5"), "name": "테스트", "count": 3}
    result = _convert_row(row)
    assert isinstance(result["salary"], float)
    assert result["salary"] == 5000.5
    assert result["name"] == "테스트"
    assert result["count"] == 3


# ━━ PYDANTIC MODELS ━━

def test_register_req():
    from models.user import RegisterReq
    r = RegisterReq(email_addr="test@example.com", password="abc123", job_nm="백엔드 개발")
    assert r.email_addr == "test@example.com"
    assert r.mbr_nm is None


def test_register_req_invalid_email():
    from models.user import RegisterReq
    try:
        RegisterReq(email_addr="not-email", password="abc", job_nm="x")
        assert False, "should raise"
    except Exception:
        pass


def test_token_resp_defaults():
    from models.user import TokenResp
    t = TokenResp(access_token="abc", mbr_id=1, mbr_nm="홍")
    assert t.token_type == "bearer"


def test_comparison_req_minimal():
    from models.comparison import ComparisonReq
    c = ComparisonReq(comp_a_tp_cd="large", comp_b_tp_cd="startup", priority_cd="salary")
    assert c.comp_a_nm is None
    assert c.salary_rate_val is None


def test_comparison_req_full():
    from models.comparison import ComparisonReq
    c = ComparisonReq(
        comp_a_nm="삼성", comp_a_tp_cd="large", salary_a_min_amt=5000,
        comp_b_nm="토스", comp_b_tp_cd="startup", salary_rate_val=20,
        priority_cd="salary", feed_points_val=["p1", "p2"]
    )
    assert c.feed_points_val == ["p1", "p2"]


def test_profiler_result_req():
    from models.profiler import ProfilerResultReq
    p = ProfilerResultReq(
        scores_val={"compensation": 8}, profile_cd="balanced",
        similarity_val=0.85, answers_val=[{"q": 1, "choice": "a"}]
    )
    assert p.job_cd is None


def test_benefit_upsert_defaults():
    from models.company import BenefitUpsert
    b = BenefitUpsert(benefit_cd="meal", benefit_nm="식대", benefit_amt=180, benefit_ctgr_cd="work_env")
    assert b.badge_cd == "est"
    assert b.sort_order_no == 0


def test_popular_case_defaults():
    from models.landing import PopularCase
    pc = PopularCase(
        case_id=1, case_type_cd="company", title_a_nm="삼성", type_a_cd="large",
        title_b_nm="토스", type_b_cd="startup"
    )
    assert pc.view_no == 0
    assert pc.comparison_no == 0


# ━━ FASTAPI INTEGRATION ━━

def test_health_endpoint():
    from fastapi.testclient import TestClient
    import main
    client = TestClient(main.app, raise_server_exceptions=False)
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_protected_endpoints_require_auth():
    from fastapi.testclient import TestClient
    import main
    client = TestClient(main.app, raise_server_exceptions=False)
    assert client.get("/api/v1/comparisons").status_code in (401, 403)
    assert client.post("/api/v1/comparisons", json={
        "comp_a_tp_cd": "large", "comp_b_tp_cd": "startup", "priority_cd": "salary"
    }).status_code in (401, 403)
    assert client.post("/api/v1/profiler/results", json={
        "scores_val": {}, "profile_cd": "b", "similarity_val": 0.5, "answers_val": []
    }).status_code in (401, 403)


def test_validation_errors():
    from fastapi.testclient import TestClient
    import main
    client = TestClient(main.app, raise_server_exceptions=False)
    assert client.get("/api/v1/companies/search").status_code == 422
    assert client.post("/api/v1/auth/register", json={
        "email_addr": "invalid", "password": "abc", "job_nm": "dev"
    }).status_code == 422
    assert client.post("/api/v1/auth/login", json={}).status_code == 422


def test_landing_ping():
    from fastapi.testclient import TestClient
    import main
    client = TestClient(main.app, raise_server_exceptions=False)
    r = client.post("/api/v1/landing/ping", json={"client_id": "test-123"})
    assert r.status_code == 200
    assert "active_visitors" in r.json()


def test_openapi_schema():
    from fastapi.testclient import TestClient
    import main
    client = TestClient(main.app, raise_server_exceptions=False)
    r = client.get("/openapi.json")
    assert r.status_code == 200
    assert len(r.json()["paths"]) >= 15


# ━━ VISITOR TRACKING ━━

def test_visitor_tracking():
    import time
    from routers.landing import _active_visitors, _get_active_count
    _active_visitors.clear()
    _active_visitors["u1"] = time.time()
    _active_visitors["u2"] = time.time()
    _active_visitors["old"] = time.time() - 120
    assert _get_active_count() == 2


# ━━ SCRAPE BENEFITS TOOL ━━

def test_scrape_resolve_company_id():
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
    from scrape_benefits import resolve_company_id
    assert resolve_company_id("삼성전자", None) == "samsung"
    assert resolve_company_id("anything", "custom") == "custom"


def test_scrape_escape_sql():
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
    from scrape_benefits import escape_sql
    assert escape_sql(None) == "NULL"
    assert "\\'" in escape_sql("test'val")


def test_scrape_parse_benefits():
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
    from scrape_benefits import parse_benefits
    bens = parse_benefits("구내식당\n조식 중식 석식 100% 제공", "test")
    assert any(b["ben_key"] == "meal" for b in bens)


# ━━ RUNNER ━━

if __name__ == "__main__":
    import traceback
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"  ✓ {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  ✗ {t.__name__}: {e}")
            traceback.print_exc()
            failed += 1
    print(f"\n{'━' * 40}")
    print(f"  {passed} passed, {failed} failed, {passed + failed} total")
    if failed:
        sys.exit(1)
