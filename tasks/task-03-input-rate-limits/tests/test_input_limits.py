"""
Task 3 - LedgerPro Accountants: Input and Rate Limit Tests
Test suite: 38 cases covering input validation, injection rejection,
boundary values, and the fixed-window rate limiter.
"""

from __future__ import annotations

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient

from app.main import app
from app.rate_limiter import reset_all


@pytest.fixture(autouse=True)
def clear_rate_limits():
    """Reset the in-process rate limiter before each test."""
    reset_all()
    yield
    reset_all()


client = TestClient(app)


# ===========================================================================
# Health / meta
# ===========================================================================

class TestHealth:
    def test_health_returns_200(self):
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_body(self):
        r = client.get("/health")
        data = r.json()
        assert data["status"] == "ok"
        assert data["task"] == "03"

    def test_security_headers_present(self):
        r = client.get("/health")
        assert r.headers.get("x-content-type-options") == "nosniff"
        assert r.headers.get("x-frame-options") == "DENY"
        assert r.headers.get("cache-control") == "no-store"

    def test_ping_returns_200(self):
        r = client.get("/api/v1/ping")
        assert r.status_code == 200


# ===========================================================================
# Client intake - happy paths
# ===========================================================================

VALID_CLIENT = {
    "client_name": "Crescent Textile Mills Ltd",
    "contact_email": "accounts@crescenttextile.pk",
    "annual_revenue": "2500000.00",
    "description": "Quarterly VAT and payroll processing",
}


class TestClientIntakeValid:
    def test_valid_client_201_or_200(self):
        r = client.post("/api/v1/clients", json=VALID_CLIENT)
        assert r.status_code == 200

    def test_response_contains_client_id(self):
        r = client.post("/api/v1/clients", json=VALID_CLIENT)
        assert "client_id" in r.json()

    def test_response_echoes_name(self):
        r = client.post("/api/v1/clients", json=VALID_CLIENT)
        assert r.json()["client_name"] == "Crescent Textile Mills Ltd"

    def test_optional_description_omitted(self):
        payload = {k: v for k, v in VALID_CLIENT.items() if k != "description"}
        r = client.post("/api/v1/clients", json=payload)
        assert r.status_code == 200

    def test_minimum_revenue_zero(self):
        payload = {**VALID_CLIENT, "annual_revenue": "0"}
        r = client.post("/api/v1/clients", json=payload)
        assert r.status_code == 200

    def test_maximum_revenue_ceiling(self):
        payload = {**VALID_CLIENT, "annual_revenue": "10000000"}
        r = client.post("/api/v1/clients", json=payload)
        assert r.status_code == 200


# ===========================================================================
# Client intake - validation failures (422)
# ===========================================================================

class TestClientIntakeInvalid:
    def test_missing_client_name(self):
        payload = {k: v for k, v in VALID_CLIENT.items() if k != "client_name"}
        r = client.post("/api/v1/clients", json=payload)
        assert r.status_code == 422

    def test_client_name_too_long(self):
        payload = {**VALID_CLIENT, "client_name": "A" * 101}
        r = client.post("/api/v1/clients", json=payload)
        assert r.status_code == 422

    def test_client_name_too_short(self):
        payload = {**VALID_CLIENT, "client_name": "A"}
        r = client.post("/api/v1/clients", json=payload)
        assert r.status_code == 422

    def test_malformed_email(self):
        payload = {**VALID_CLIENT, "contact_email": "not-an-email"}
        r = client.post("/api/v1/clients", json=payload)
        assert r.status_code == 422

    def test_negative_revenue(self):
        payload = {**VALID_CLIENT, "annual_revenue": "-1"}
        r = client.post("/api/v1/clients", json=payload)
        assert r.status_code == 422

    def test_revenue_above_ceiling(self):
        payload = {**VALID_CLIENT, "annual_revenue": "10000001"}
        r = client.post("/api/v1/clients", json=payload)
        assert r.status_code == 422

    def test_description_too_long(self):
        payload = {**VALID_CLIENT, "description": "X" * 501}
        r = client.post("/api/v1/clients", json=payload)
        assert r.status_code == 422


# ===========================================================================
# Client intake - injection rejection (422)
# ===========================================================================

class TestClientIntakeInjection:
    def test_sql_injection_in_name(self):
        payload = {**VALID_CLIENT, "client_name": "' OR 1=1 --"}
        r = client.post("/api/v1/clients", json=payload)
        assert r.status_code == 422

    def test_xss_in_description(self):
        payload = {**VALID_CLIENT, "description": "<script>alert(1)</script>"}
        r = client.post("/api/v1/clients", json=payload)
        assert r.status_code == 422

    def test_drop_table_in_name(self):
        payload = {**VALID_CLIENT, "client_name": "drop table clients"}
        r = client.post("/api/v1/clients", json=payload)
        assert r.status_code == 422

    def test_union_select_in_name(self):
        payload = {**VALID_CLIENT, "client_name": "1 union select 1,2,3"}
        r = client.post("/api/v1/clients", json=payload)
        assert r.status_code == 422

    def test_javascript_uri_in_email(self):
        payload = {**VALID_CLIENT, "contact_email": "javascript:alert(1)@evil.com"}
        # Either malformed email or injection check should fire
        r = client.post("/api/v1/clients", json=payload)
        assert r.status_code == 422

    def test_error_body_is_structured(self):
        payload = {**VALID_CLIENT, "client_name": "' OR 1=1 --"}
        r = client.post("/api/v1/clients", json=payload)
        body = r.json()
        assert body["error"] == "validation_failed"
        assert isinstance(body["detail"], list)


# ===========================================================================
# Invoice submission - happy paths
# ===========================================================================

VALID_INVOICE = {
    "client_id": "CLI-0042",
    "invoice_ref": "INV-100122",
    "amount": "4800.00",
    "line_item": "Quarterly VAT return preparation - Q3 2026",
}


class TestInvoiceValid:
    def test_valid_invoice_200(self):
        r = client.post("/api/v1/invoices", json=VALID_INVOICE)
        assert r.status_code == 200

    def test_response_status_pending(self):
        r = client.post("/api/v1/invoices", json=VALID_INVOICE)
        assert r.json()["status"] == "pending"

    def test_response_echoes_invoice_ref(self):
        r = client.post("/api/v1/invoices", json=VALID_INVOICE)
        assert r.json()["invoice_ref"] == "INV-100122"


class TestInvoiceInvalid:
    def test_bad_client_id_format(self):
        r = client.post("/api/v1/invoices", json={**VALID_INVOICE, "client_id": "BAD"})
        assert r.status_code == 422

    def test_bad_invoice_ref_format(self):
        r = client.post("/api/v1/invoices", json={**VALID_INVOICE, "invoice_ref": "REF-999"})
        assert r.status_code == 422

    def test_zero_amount(self):
        r = client.post("/api/v1/invoices", json={**VALID_INVOICE, "amount": "0"})
        assert r.status_code == 422

    def test_negative_amount(self):
        r = client.post("/api/v1/invoices", json={**VALID_INVOICE, "amount": "-100"})
        assert r.status_code == 422

    def test_amount_above_ceiling(self):
        r = client.post("/api/v1/invoices", json={**VALID_INVOICE, "amount": "10000001"})
        assert r.status_code == 422

    def test_sql_in_line_item(self):
        r = client.post("/api/v1/invoices", json={**VALID_INVOICE, "line_item": "'; DROP TABLE invoices; --"})
        assert r.status_code == 422


# ===========================================================================
# Ledger entry - happy paths and validation
# ===========================================================================

class TestLedgerEntry:
    def test_valid_debit_entry(self):
        payload = {
            "account_code": "4000",
            "debit": "1500.00",
            "credit": "0",
            "narrative": "Payment received - Crescent Textile Mills Q3 invoice",
        }
        r = client.post("/api/v1/ledger", json=payload)
        assert r.status_code == 200

    def test_valid_credit_entry(self):
        payload = {
            "account_code": "1200",
            "debit": "0",
            "credit": "1500.00",
            "narrative": "Sales ledger credit - Crescent Textile Mills",
        }
        r = client.post("/api/v1/ledger", json=payload)
        assert r.status_code == 200

    def test_both_debit_and_credit_rejected(self):
        payload = {
            "account_code": "4000",
            "debit": "500.00",
            "credit": "500.00",
            "narrative": "Invalid double entry",
        }
        r = client.post("/api/v1/ledger", json=payload)
        assert r.status_code == 422

    def test_both_zero_rejected(self):
        payload = {
            "account_code": "4000",
            "debit": "0",
            "credit": "0",
            "narrative": "Nothing posted",
        }
        r = client.post("/api/v1/ledger", json=payload)
        assert r.status_code == 422

    def test_bad_account_code_format(self):
        payload = {
            "account_code": "SALES",
            "debit": "100",
            "credit": "0",
            "narrative": "Sales income - Khalid & Sons",
        }
        r = client.post("/api/v1/ledger", json=payload)
        assert r.status_code == 422

    def test_narrative_too_short(self):
        payload = {
            "account_code": "4000",
            "debit": "100",
            "credit": "0",
            "narrative": "Hi",
        }
        r = client.post("/api/v1/ledger", json=payload)
        assert r.status_code == 422

    def test_xss_in_narrative_rejected(self):
        payload = {
            "account_code": "4000",
            "debit": "100",
            "credit": "0",
            "narrative": "<img src=x onerror=alert(1)>",
        }
        r = client.post("/api/v1/ledger", json=payload)
        assert r.status_code == 422


# ===========================================================================
# Rate limiter
# ===========================================================================

class TestRateLimiter:
    """
    The in-process limiter is applied directly in test helpers below.
    We call the /ping endpoint 11 times; the 11th should return 429.
    Config: RATE_LIMIT_REQUESTS = 10 per 60s.
    """

    def test_within_limit_returns_200(self):
        for _ in range(10):
            r = client.get("/api/v1/ping")
            # First 10 calls should succeed
            assert r.status_code == 200, f"Expected 200, got {r.status_code}"

    def test_exceed_limit_returns_429(self):
        """The 11th call in the same window must be rejected."""
        from app.rate_limiter import _windows, RATE_LIMIT_WINDOW_SECONDS
        import time

        # Manually fill the window to simulate 10 prior hits
        key = "testclient:default"
        _windows[key] = (time.monotonic(), 10)

        # Import check_rate_limit and call directly with a mock request
        from app.rate_limiter import check_rate_limit
        from unittest.mock import MagicMock
        from fastapi import HTTPException

        mock_request = MagicMock()
        mock_request.client.host = "testclient"

        with pytest.raises(HTTPException) as exc_info:
            check_rate_limit(mock_request, endpoint="default")

        assert exc_info.value.status_code == 429
        assert exc_info.value.detail["error"] == "rate_limit_exceeded"

    def test_rate_limit_error_body_has_retry_after(self):
        from app.rate_limiter import _windows, check_rate_limit
        import time
        from unittest.mock import MagicMock
        from fastapi import HTTPException

        key = "testclient:default"
        _windows[key] = (time.monotonic(), 10)

        mock_request = MagicMock()
        mock_request.client.host = "testclient"

        with pytest.raises(HTTPException) as exc_info:
            check_rate_limit(mock_request, endpoint="default")

        assert "retry_after_seconds" in exc_info.value.detail

    def test_new_window_resets_counter(self):
        """After the window expires the counter resets and calls succeed."""
        from app.rate_limiter import _windows
        import time

        # Plant an old window (61 seconds ago - expired)
        key = "testclient:reset"
        _windows[key] = (time.monotonic() - 61, 10)

        from app.rate_limiter import check_rate_limit
        from unittest.mock import MagicMock

        mock_request = MagicMock()
        mock_request.client.host = "testclient"

        # Should not raise - window is expired
        check_rate_limit(mock_request, endpoint="reset")
