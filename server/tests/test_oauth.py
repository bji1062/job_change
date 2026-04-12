"""
OAuth + Company Email Verification test suite for Job Choice OS.
Run: cd server && JWT_SECRET=test_secret python -m pytest tests/test_oauth.py -v
  or: cd server && JWT_SECRET=test_secret python tests/test_oauth.py

Strategy: Mock database.* and httpx calls at module level
so no real DB or external API connection is needed.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import AsyncMock, patch, MagicMock
from services.auth_service import create_token


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _user_token(mbr_id: int = 1, cev: bool = False) -> dict:
    """Return Authorization header with regular user JWT."""
    token = create_token(mbr_id, role_cd="user", cev=cev)
    return {"Authorization": f"Bearer {token}"}

def _verified_user_token(mbr_id: int = 1) -> dict:
    """Return Authorization header with company-email-verified user JWT."""
    return _user_token(mbr_id=mbr_id, cev=True)

def _admin_token(mbr_id: int = 99) -> dict:
    """Return Authorization header with admin JWT."""
    token = create_token(mbr_id, role_cd="admin")
    return {"Authorization": f"Bearer {token}"}

def _client():
    """Create a TestClient with server exceptions suppressed."""
    from fastapi.testclient import TestClient
    import main
    return TestClient(main.app, raise_server_exceptions=False)


# ━━ OAUTH LOGIN REDIRECT ━━

def test_oauth_kakao_login_redirects():
    """GET /oauth/kakao/login returns 302 redirect to Kakao auth URL."""
    with patch("config.KAKAO_CLIENT_ID", "test_kakao_id"):
        c = _client()
        r = c.get("/api/v1/oauth/kakao/login", follow_redirects=False)
        assert r.status_code in (302, 307), f"Expected redirect, got {r.status_code}"
        location = r.headers.get("location", "")
        assert "kauth.kakao.com" in location


def test_oauth_naver_login_redirects():
    """GET /oauth/naver/login returns 302 redirect to Naver auth URL."""
    with patch("config.NAVER_CLIENT_ID", "test_naver_id"):
        c = _client()
        r = c.get("/api/v1/oauth/naver/login", follow_redirects=False)
        assert r.status_code in (302, 307)
        location = r.headers.get("location", "")
        assert "nid.naver.com" in location


def test_oauth_google_login_redirects():
    """GET /oauth/google/login returns 302 redirect to Google auth URL."""
    with patch("config.GOOGLE_CLIENT_ID", "test_google_id"):
        c = _client()
        r = c.get("/api/v1/oauth/google/login", follow_redirects=False)
        assert r.status_code in (302, 307)
        location = r.headers.get("location", "")
        assert "accounts.google.com" in location


def test_oauth_invalid_provider_returns_400():
    """GET /oauth/twitter/login returns 400 for unsupported provider."""
    c = _client()
    r = c.get("/api/v1/oauth/twitter/login")
    assert r.status_code == 400
    assert "지원하지 않는" in r.json()["detail"]


# ━━ OAUTH CALLBACK ━━

def test_oauth_callback_missing_code_returns_422():
    """GET /oauth/kakao/callback without code query param returns 422."""
    c = _client()
    r = c.get("/api/v1/oauth/kakao/callback")
    assert r.status_code == 422


def test_oauth_callback_invalid_state_returns_400():
    """GET /oauth/kakao/callback with invalid state returns 400."""
    c = _client()
    r = c.get("/api/v1/oauth/kakao/callback?code=testcode&state=invalid_state")
    assert r.status_code == 400


# ━━ OAUTH ME ━━

def test_oauth_me_without_token_returns_403():
    """GET /oauth/me without token returns 403 (HTTPBearer auto-rejects)."""
    c = _client()
    r = c.get("/api/v1/oauth/me")
    assert r.status_code == 403


def test_oauth_me_invalid_token_returns_401():
    """GET /oauth/me with garbage token returns 401."""
    c = _client()
    r = c.get("/api/v1/oauth/me", headers={"Authorization": "Bearer garbage.token"})
    assert r.status_code == 401


@patch("database.fetch_one", new_callable=AsyncMock, return_value={"mbr_id": 1, "email_addr": "user@test.com", "mbr_nm": "Tester", "role_cd": "user", "login_provider_cd": "kakao", "comp_email_addr": None, "comp_email_vrfc_yn": "N"})
def test_oauth_me_with_valid_token(mock_fetch):
    """GET /oauth/me with valid token returns 200 and user info."""
    c = _client()
    r = c.get("/api/v1/oauth/me", headers=_user_token(mbr_id=1))
    assert r.status_code == 200
    data = r.json()
    assert data["mbr_id"] == 1
    assert data["email_addr"] == "user@test.com"


# ━━ COMPANY EMAIL REQUEST ━━

def test_company_email_request_without_token_returns_403():
    """POST /oauth/company-email/request without token returns 403."""
    c = _client()
    r = c.post("/api/v1/oauth/company-email/request", json={"email_addr": "user@samsung.com"})
    assert r.status_code == 403


def test_company_email_request_personal_email_returns_400():
    """POST /oauth/company-email/request with gmail.com returns 400."""
    c = _client()
    r = c.post(
        "/api/v1/oauth/company-email/request",
        json={"email_addr": "user@gmail.com"},
        headers=_user_token(mbr_id=1),
    )
    assert r.status_code == 400
    assert "회사 이메일" in r.json()["detail"]


@patch("services.auth_service.send_verification_email", new_callable=AsyncMock, return_value=None)
@patch("database.execute", new_callable=AsyncMock, return_value=1)
def test_company_email_request_success(mock_exec, mock_send):
    """POST /oauth/company-email/request with company email succeeds."""
    c = _client()
    r = c.post(
        "/api/v1/oauth/company-email/request",
        json={"email_addr": "user@samsung.com"},
        headers=_user_token(mbr_id=1),
    )
    assert r.status_code == 200
    assert r.json()["ok"] is True
    # 2 calls: invalidate old tokens + insert new verification
    assert mock_exec.call_count == 2


@patch("services.auth_service.send_verification_email", new_callable=AsyncMock, return_value=None)
@patch("database.execute", new_callable=AsyncMock, return_value=1)
def test_company_email_rejects_naver(mock_exec, mock_send):
    """POST /oauth/company-email/request with naver.com returns 400."""
    c = _client()
    r = c.post(
        "/api/v1/oauth/company-email/request",
        json={"email_addr": "user@naver.com"},
        headers=_user_token(mbr_id=1),
    )
    assert r.status_code == 400


# ━━ COMPANY EMAIL VERIFY ━━

@patch("database.fetch_one", new_callable=AsyncMock, return_value=None)
def test_company_email_verify_invalid_token(mock_fetch):
    """GET /oauth/company-email/verify with bad token returns 400."""
    c = _client()
    r = c.get("/api/v1/oauth/company-email/verify?token=bad_token_123", follow_redirects=False)
    assert r.status_code == 400
    assert "유효하지 않" in r.json()["detail"]


@patch("database.execute", new_callable=AsyncMock, return_value=None)
@patch("database.fetch_one", new_callable=AsyncMock, return_value={
    "verify_id": 10, "mbr_id": 1, "email_addr": "user@samsung.com",
})
def test_company_email_verify_success(mock_fetch, mock_exec):
    """GET /oauth/company-email/verify with valid token updates user and redirects."""
    c = _client()
    r = c.get(
        "/api/v1/oauth/company-email/verify?token=valid_token_abc",
        follow_redirects=False,
    )
    # Should redirect to frontend with email_verified=1
    assert r.status_code in (302, 307), f"Expected redirect, got {r.status_code}"
    location = r.headers.get("location", "")
    assert "email_verified=1" in location
    # Verify DB calls: update email_verifications + update users
    assert mock_exec.call_count == 2


# ━━ PERMISSION: get_verified_user (PUT /companies/{id}/benefits) ━━

def test_benefits_upsert_no_token_returns_403():
    """PUT /companies/{id}/benefits without token returns 403."""
    c = _client()
    r = c.put(
        "/api/v1/companies/1/benefits",
        json=[{"benefit_cd": "meal", "benefit_nm": "Meal", "benefit_amt": 100, "benefit_ctgr_cd": "work_env"}],
    )
    assert r.status_code == 403


def test_benefits_upsert_unverified_user_returns_403():
    """PUT /companies/{id}/benefits with unverified user (cev=false) returns 403."""
    c = _client()
    r = c.put(
        "/api/v1/companies/1/benefits",
        json=[{"benefit_cd": "meal", "benefit_nm": "Meal", "benefit_amt": 100, "benefit_ctgr_cd": "work_env"}],
        headers=_user_token(mbr_id=1, cev=False),
    )
    assert r.status_code == 403
    assert "이메일 인증" in r.json()["detail"]


@patch("database.fetch_all", new_callable=AsyncMock, return_value=[
    {"benefit_cd": "meal", "benefit_nm": "Meal", "benefit_amt": 100.0, "benefit_ctgr_cd": "work_env", "badge_cd": "est", "note_ctnt": None, "qual_yn": 0, "qual_desc_ctnt": None},
])
@patch("database.execute", new_callable=AsyncMock, return_value=None)
@patch("database.fetch_one", new_callable=AsyncMock, return_value={"id": 1})
def test_benefits_upsert_verified_user_succeeds(mock_one, mock_exec, mock_all):
    """PUT /companies/{id}/benefits with verified user (cev=true) returns 200."""
    c = _client()
    r = c.put(
        "/api/v1/companies/1/benefits",
        json=[{"benefit_cd": "meal", "benefit_nm": "Meal", "benefit_amt": 100, "benefit_ctgr_cd": "work_env"}],
        headers=_verified_user_token(mbr_id=1),
    )
    assert r.status_code == 200
    assert r.json()["count"] == 1


@patch("database.fetch_all", new_callable=AsyncMock, return_value=[
    {"benefit_cd": "meal", "benefit_nm": "Meal", "benefit_amt": 100.0, "benefit_ctgr_cd": "work_env", "badge_cd": "est", "note_ctnt": None, "qual_yn": 0, "qual_desc_ctnt": None},
])
@patch("database.execute", new_callable=AsyncMock, return_value=None)
@patch("database.fetch_one", new_callable=AsyncMock, return_value={"id": 1})
def test_benefits_upsert_admin_succeeds(mock_one, mock_exec, mock_all):
    """PUT /companies/{id}/benefits with admin token returns 200 (admin bypass)."""
    c = _client()
    r = c.put(
        "/api/v1/companies/1/benefits",
        json=[{"benefit_cd": "meal", "benefit_nm": "Meal", "benefit_amt": 100, "benefit_ctgr_cd": "work_env"}],
        headers=_admin_token(),
    )
    assert r.status_code == 200
    assert r.json()["count"] == 1


# ━━ AUTH LOGIN COMPAT ━━

@patch("database.fetch_one", new_callable=AsyncMock, return_value={"mbr_id": 1, "pwd_hash_val": "$2b$12$test_hash", "mbr_nm": "Tester", "role_cd": "user", "comp_email_vrfc_yn": "N"})
@patch("routers.auth.verify_password", return_value=True)
def test_login_email_password_works(mock_verify, mock_fetch):
    """POST /auth/login with correct email/password returns token."""
    c = _client()
    r = c.post("/api/v1/auth/login", json={"email_addr": "user@test.com", "password": "pass123"})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["mbr_id"] == 1
    assert "comp_email_vrfc_yn" in data


@patch("database.fetch_one", new_callable=AsyncMock, return_value={
    "mbr_id": 2, "pwd_hash_val": None, "mbr_nm": "Social User",
    "role_cd": "user", "comp_email_vrfc_yn": "N",
})
def test_login_social_account_no_password_returns_401(mock_fetch):
    """POST /auth/login for social account (pwd_hash_val=NULL) returns 401."""
    c = _client()
    r = c.post("/api/v1/auth/login", json={"email_addr": "social@test.com", "password": "anything"})
    assert r.status_code == 401
    assert "Invalid credentials" in r.json()["detail"]


@patch("database.fetch_one", new_callable=AsyncMock, return_value={"mbr_id": 1, "pwd_hash_val": "$2b$12$test_hash", "mbr_nm": "Verified", "role_cd": "user", "comp_email_vrfc_yn": "Y"})
@patch("routers.auth.verify_password", return_value=True)
def test_login_returns_cev_true_when_verified(mock_verify, mock_fetch):
    """POST /auth/login includes comp_email_vrfc_yn=true in response."""
    c = _client()
    r = c.post("/api/v1/auth/login", json={"email_addr": "v@samsung.com", "password": "pass"})
    assert r.status_code == 200
    data = r.json()
    assert data["comp_email_vrfc_yn"] is True


# ━━ FRONTEND PATH VALIDATION ━━

def test_no_double_api_prefix_in_frontend():
    """apiFetch() calls should not contain /api/v1/ prefix (auto-added)."""
    import re
    html_path = os.path.join(os.path.dirname(__file__), "..", "..", "index.html")
    with open(html_path) as f:
        content = f.read()
    matches = re.findall(r"apiFetch\s*\(\s*['\"]\/api\/v1\/", content)
    assert len(matches) == 0, f"Double prefix bug found ({len(matches)}): {matches}"


# ━━ OAUTH PARSE USERINFO ━━

def test_parse_userinfo_kakao():
    """_parse_userinfo correctly parses Kakao response."""
    from routers.oauth import _parse_userinfo
    data = {
        "id": 12345,
        "kakao_account": {
            "email": "user@kakao.com",
            "is_email_verified": True,
            "profile": {"nickname": "KakaoUser"},
        },
    }
    pid, email, name, ev = _parse_userinfo("kakao", data)
    assert pid == "12345"
    assert email == "user@kakao.com"
    assert name == "KakaoUser"
    assert ev is True


def test_parse_userinfo_naver():
    """_parse_userinfo correctly parses Naver response."""
    from routers.oauth import _parse_userinfo
    data = {
        "response": {
            "id": "naver_abc",
            "email": "user@naver.com",
            "name": "NaverUser",
        },
    }
    pid, email, name, ev = _parse_userinfo("naver", data)
    assert pid == "naver_abc"
    assert email == "user@naver.com"
    assert name == "NaverUser"
    assert ev is True  # Naver emails are always verified


def test_parse_userinfo_google():
    """_parse_userinfo correctly parses Google response."""
    from routers.oauth import _parse_userinfo
    data = {
        "id": "google_xyz",
        "email": "user@gmail.com",
        "verified_email": True,
        "name": "GoogleUser",
    }
    pid, email, name, ev = _parse_userinfo("google", data)
    assert pid == "google_xyz"
    assert email == "user@gmail.com"
    assert name == "GoogleUser"
    assert ev is True


# ━━ OAUTH ME: USER NOT FOUND ━━

@patch("database.fetch_one", new_callable=AsyncMock, return_value=None)
def test_oauth_me_user_not_found_returns_404(mock_fetch):
    """GET /oauth/me returns 404 if user deleted from DB."""
    c = _client()
    r = c.get("/api/v1/oauth/me", headers=_user_token(mbr_id=999))
    assert r.status_code == 404


# ━━ CALLBACK: MISSING STATE ONLY ━━

def test_oauth_callback_missing_state_returns_422():
    """GET /oauth/kakao/callback with code but no state returns 422."""
    c = _client()
    r = c.get("/api/v1/oauth/kakao/callback?code=test_code")
    assert r.status_code == 422


# ━━ COMPANY EMAIL: EDGE CASES ━━

def test_company_email_request_invalid_email_format():
    """POST /oauth/company-email/request with invalid email returns 422."""
    c = _client()
    r = c.post(
        "/api/v1/oauth/company-email/request",
        json={"email_addr": "not-an-email"},
        headers=_user_token(),
    )
    assert r.status_code == 422


@patch("services.auth_service.send_verification_email", new_callable=AsyncMock, return_value=None)
@patch("database.execute", new_callable=AsyncMock, return_value=1)
def test_company_email_request_custom_domain_succeeds(mock_exec, mock_send):
    """POST /oauth/company-email/request with toss.im succeeds."""
    c = _client()
    r = c.post(
        "/api/v1/oauth/company-email/request",
        json={"email_addr": "dev@toss.im"},
        headers=_user_token(),
    )
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_company_email_verify_missing_token_param():
    """GET /oauth/company-email/verify without token query returns 422."""
    c = _client()
    r = c.get("/api/v1/oauth/company-email/verify")
    assert r.status_code == 422


# ━━ TOKEN RESP MODEL ━━

def test_token_resp_includes_cev_field():
    """TokenResp model includes comp_email_vrfc_yn field with default False."""
    from models.user import TokenResp
    t = TokenResp(access_token="tok", mbr_id=1, mbr_nm="A", comp_email_vrfc_yn=True)
    assert t.comp_email_vrfc_yn is True
    t2 = TokenResp(access_token="tok", mbr_id=2, mbr_nm="B")
    assert t2.comp_email_vrfc_yn is False


# ━━ LOGIN: WRONG PASSWORD ━━

@patch("database.fetch_one", new_callable=AsyncMock, return_value={"mbr_id": 1, "pwd_hash_val": "$2b$12$somehash", "mbr_nm": "User", "role_cd": "user", "comp_email_vrfc_yn": "N"})
@patch("routers.auth.verify_password", return_value=False)
def test_login_wrong_password_returns_401(mock_verify, mock_fetch):
    """POST /auth/login with wrong password returns 401."""
    c = _client()
    r = c.post("/api/v1/auth/login", json={
        "email_addr": "user@example.com",
        "password": "wrong_password",
    })
    assert r.status_code == 401


# ━━ UNIT: is_company_email ━━

def test_is_company_email_rejects_personal():
    """is_company_email returns False for personal domains."""
    from services.auth_service import is_company_email
    for domain in ["gmail.com", "naver.com", "kakao.com", "hotmail.com", "icloud.com"]:
        assert is_company_email(f"user@{domain}") is False, f"{domain} should be personal"


def test_is_company_email_accepts_corporate():
    """is_company_email returns True for corporate domains."""
    from services.auth_service import is_company_email
    for domain in ["samsung.com", "lg.com", "kakaocorp.com", "navercorp.com", "sk.com"]:
        assert is_company_email(f"user@{domain}") is True, f"{domain} should be corporate"


# ━━ UNIT: create_token with cev ━━

def test_create_token_includes_cev_claim():
    """create_token with cev=True sets cev=True in JWT payload."""
    from services.auth_service import create_token, decode_token_full
    token = create_token(1, role_cd="user", cev=True)
    payload = decode_token_full(token)
    assert payload is not None
    assert payload["cev"] is True


def test_create_token_cev_defaults_false():
    """create_token without cev sets cev=False in JWT payload."""
    from services.auth_service import create_token, decode_token_full
    token = create_token(1, role_cd="user")
    payload = decode_token_full(token)
    assert payload is not None
    assert payload["cev"] is False


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
    print(f"\n{'=' * 40}")
    print(f"  {passed} passed, {failed} failed, {passed + failed} total")
    if failed:
        sys.exit(1)
