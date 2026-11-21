"""
Task 2 Automated Test Suite - LedgerPro Accountants Auth & Token Checks
Covers:
  - Happy paths: login, refresh, /me, role-protected resources
  - Security failure paths: bad credentials, expired token, tampered token,
    wrong token type, disabled account, role boundary enforcement, empty inputs
"""

import time
import pytest
from datetime import timedelta
from fastapi.testclient import TestClient
from jose import jwt

from app.main import app
from app.auth.jwt_handler import create_access_token, create_refresh_token, decode_token
from app.config import SECRET_KEY, ALGORITHM

client = TestClient(app, raise_server_exceptions=False)

# ── Credential fixtures (match users.py seed data exactly) ─────────────────
ADMIN    = {"username": "fatima.zahra",  "password": "FatimaSecure#2026"}
AUDITOR  = {"username": "tariq.mahmood", "password": "TariqAudit@2026"}
ACCOUNTANT = {"username": "zainab.ali",  "password": "ZainabTax!2026"}
VIEWER   = {"username": "bilal.khan",    "password": "BilalView@2026"}
INACTIVE = {"username": "khalid.mansoor", "password": "OldPass#2024"}


def login_as(creds: dict) -> dict:
    """Helper: log in and return the full token response dict."""
    r = client.post("/api/v1/auth/login", json=creds)
    assert r.status_code == 200, f"Login failed: {r.text}"
    return r.json()


# ═══════════════════════════════════════════════════════════════════════════
# 1. SYSTEM HEALTH & SECURITY HEADERS
# ═══════════════════════════════════════════════════════════════════════════

def test_health_endpoint():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_security_headers_present():
    r = client.get("/health")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert r.headers["server"] == "LedgerPro-Lab-Engine"


def test_auth_responses_not_cached():
    """Login responses must carry Cache-Control: no-store to prevent browser caching of tokens."""
    r = client.post("/api/v1/auth/login", json=ADMIN)
    assert "no-store" in r.headers.get("cache-control", "")


# ═══════════════════════════════════════════════════════════════════════════
# 2. LOGIN - HAPPY PATHS
# ═══════════════════════════════════════════════════════════════════════════

def test_admin_login_returns_tokens():
    data = login_as(ADMIN)
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "admin"
    assert data["username"] == "fatima.zahra"
    assert data["expires_in_seconds"] == 900  # 15 min


def test_auditor_login_returns_correct_role():
    data = login_as(AUDITOR)
    assert data["role"] == "auditor"


def test_accountant_login_returns_correct_role():
    data = login_as(ACCOUNTANT)
    assert data["role"] == "accountant"


def test_viewer_login_returns_correct_role():
    data = login_as(VIEWER)
    assert data["role"] == "viewer"


def test_access_token_contains_expected_claims():
    """The JWT payload must carry sub, role, exp, iat, and type=access."""
    data = login_as(ADMIN)
    claims = decode_token(data["access_token"])
    assert claims["sub"] == "fatima.zahra"
    assert claims["role"] == "admin"
    assert claims["type"] == "access"
    assert "exp" in claims
    assert "iat" in claims


def test_refresh_token_type_claim_is_refresh():
    """Refresh token must have type='refresh', not 'access'."""
    data = login_as(ADMIN)
    claims = decode_token(data["refresh_token"])
    assert claims["type"] == "refresh"


# ═══════════════════════════════════════════════════════════════════════════
# 3. /ME - AUTHENTICATED PROFILE
# ═══════════════════════════════════════════════════════════════════════════

def test_me_returns_correct_profile():
    tokens = login_as(AUDITOR)
    r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert r.status_code == 200
    data = r.json()
    assert data["username"] == "tariq.mahmood"
    assert data["role"] == "auditor"
    assert data["department"] == "Statutory Audit & Assurance"
    assert "@ledgerpro.com" in data["email"]


# ═══════════════════════════════════════════════════════════════════════════
# 4. TOKEN REFRESH - HAPPY PATH
# ═══════════════════════════════════════════════════════════════════════════

def test_refresh_issues_new_access_token():
    tokens = login_as(ADMIN)
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 200
    new_tokens = r.json()
    assert "access_token" in new_tokens
    # New access token is different from the original
    assert new_tokens["access_token"] != tokens["access_token"]


# ═══════════════════════════════════════════════════════════════════════════
# 5. ROLE-BASED ACCESS CONTROL - HAPPY PATHS
# ═══════════════════════════════════════════════════════════════════════════

def test_admin_can_access_ledger_report():
    tokens = login_as(ADMIN)
    r = client.get("/api/v1/auth/resources/ledger-report",
                   headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert r.status_code == 200
    assert r.json()["data"]["ledger_balanced"] is True


def test_auditor_can_access_ledger_report():
    tokens = login_as(AUDITOR)
    r = client.get("/api/v1/auth/resources/ledger-report",
                   headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert r.status_code == 200


def test_accountant_can_access_client_list():
    tokens = login_as(ACCOUNTANT)
    r = client.get("/api/v1/auth/resources/client-list",
                   headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert r.status_code == 200
    assert len(r.json()["clients"]) == 5


def test_all_roles_can_access_public_rates():
    for creds in [ADMIN, AUDITOR, ACCOUNTANT, VIEWER]:
        tokens = login_as(creds)
        r = client.get("/api/v1/auth/resources/public-rates",
                       headers={"Authorization": f"Bearer {tokens['access_token']}"})
        assert r.status_code == 200, f"Failed for {creds['username']}"


# ═══════════════════════════════════════════════════════════════════════════
# 6. AUTHENTICATION FAILURE PATHS
# ═══════════════════════════════════════════════════════════════════════════

def test_wrong_password_returns_401():
    r = client.post("/api/v1/auth/login", json={"username": "fatima.zahra", "password": "WrongPassword"})
    assert r.status_code == 401


def test_nonexistent_user_returns_401():
    r = client.post("/api/v1/auth/login", json={"username": "ghost.user", "password": "doesntmatter"})
    assert r.status_code == 401


def test_wrong_and_nonexistent_return_identical_message():
    """
    Username enumeration prevention: both wrong-password and unknown-user
    must return the exact same error message so an attacker cannot distinguish
    between 'user does not exist' and 'user exists but password is wrong'.
    """
    r_bad_pass = client.post("/api/v1/auth/login",
                              json={"username": "fatima.zahra", "password": "WrongPassword"})
    r_no_user = client.post("/api/v1/auth/login",
                             json={"username": "ghost.user", "password": "WrongPassword"})
    assert r_bad_pass.json()["message"] == r_no_user.json()["message"]


def test_disabled_account_blocked_even_with_correct_password():
    """
    Inactive/offboarded staff must be rejected at login with 403,
    even when the password is correct.
    """
    r = client.post("/api/v1/auth/login", json=INACTIVE)
    assert r.status_code == 403


def test_empty_login_payload_returns_422():
    r = client.post("/api/v1/auth/login", json={})
    assert r.status_code == 422
    data = r.json()
    assert data["error_code"] == "INPUT_VALIDATION_ERROR"


def test_missing_bearer_token_returns_401():
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401


def test_malformed_token_returns_401():
    r = client.get("/api/v1/auth/me",
                   headers={"Authorization": "Bearer this.is.not.a.jwt"})
    assert r.status_code == 401


def test_expired_token_returns_401():
    """
    Issue a token with exp already in the past (-1 second).
    The API must reject it with 401, never serve the resource.
    """
    expired_token = create_access_token(
        data={"sub": "fatima.zahra", "role": "admin"},
        expires_delta=timedelta(seconds=-1),
    )
    r = client.get("/api/v1/auth/me",
                   headers={"Authorization": f"Bearer {expired_token}"})
    assert r.status_code == 401


def test_tampered_signature_returns_401():
    """
    Take a valid token, modify one character in the signature segment.
    The API must reject it - the HMAC verification must fail.
    """
    tokens = login_as(ADMIN)
    valid = tokens["access_token"]
    header, payload_part, sig = valid.rsplit(".", 2)
    # Flip first character of signature
    tampered_sig = ("A" if sig[0] != "A" else "B") + sig[1:]
    tampered = f"{header}.{payload_part}.{tampered_sig}"
    r = client.get("/api/v1/auth/me",
                   headers={"Authorization": f"Bearer {tampered}"})
    assert r.status_code == 401


def test_refresh_token_rejected_as_access_token():
    """
    Supplying a refresh token to a resource endpoint (which expects an access token)
    must be rejected. Type confusion is a real attack vector.
    """
    tokens = login_as(ADMIN)
    r = client.get("/api/v1/auth/me",
                   headers={"Authorization": f"Bearer {tokens['refresh_token']}"})
    assert r.status_code == 401


def test_access_token_rejected_as_refresh_token():
    """
    Supplying an access token to the /refresh endpoint must fail - wrong type.
    """
    tokens = login_as(ADMIN)
    r = client.post("/api/v1/auth/refresh",
                    json={"refresh_token": tokens["access_token"]})
    assert r.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════
# 7. RBAC ENFORCEMENT - FAILURE PATHS
# ═══════════════════════════════════════════════════════════════════════════

def test_viewer_cannot_access_ledger_report():
    """Viewer role must be denied access to auditor-only resource."""
    tokens = login_as(VIEWER)
    r = client.get("/api/v1/auth/resources/ledger-report",
                   headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert r.status_code == 403


def test_viewer_cannot_access_client_list():
    tokens = login_as(VIEWER)
    r = client.get("/api/v1/auth/resources/client-list",
                   headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert r.status_code == 403


def test_accountant_cannot_access_ledger_report():
    """Ledger report requires auditor or admin - accountant must be denied."""
    tokens = login_as(ACCOUNTANT)
    r = client.get("/api/v1/auth/resources/ledger-report",
                   headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert r.status_code == 403


# ═══════════════════════════════════════════════════════════════════════════
# 8. TOKEN INSPECTOR (SECURITY AUDIT TOOL)
# ═══════════════════════════════════════════════════════════════════════════

def test_inspect_valid_token_returns_claims():
    tokens = login_as(ADMIN)
    r = client.post("/api/v1/auth/inspect",
                    json={"refresh_token": tokens["access_token"]})
    assert r.status_code == 200
    data = r.json()
    assert data["subject"] == "fatima.zahra"
    assert data["token_type"] == "access"
    assert data["is_expired"] is False


def test_inspect_expired_token_reports_expired():
    expired = create_access_token(
        data={"sub": "tariq.mahmood", "role": "auditor"},
        expires_delta=timedelta(seconds=-1),
    )
    r = client.post("/api/v1/auth/inspect", json={"refresh_token": expired})
    assert r.status_code == 200
    assert r.json()["is_expired"] is True
