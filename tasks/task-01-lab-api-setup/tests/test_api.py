"""
Unit & Integration Test Suite for LedgerPro Accountants Lab API.
Validates:
1. Health and System Endpoints
2. Happy Paths for Clients, Invoicing, and General Ledger
3. Failure Paths, Malformed Inputs, and Business Rule Enforcements
4. Crash Prevention & Structured Error Payloads
5. Security Headers
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.data.mock_db import db


@pytest.fixture(autouse=True)
def reset_db_before_test():
    """Ensure every test runs against a fresh baseline seed database."""
    db.reset()
    yield


client = TestClient(app)


# ==========================================
# 1. System Health & Security Headers Tests
# ==========================================

def test_health_check_endpoint():
    """Verify system health endpoint returns 200 with operational metadata."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["version"] == "1.0.0"


def test_security_headers_enforced():
    """Verify core OWASP defense headers are present on all API responses."""
    response = client.get("/health")
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("server") == "LedgerPro-Lab-Engine"


# ==========================================
# 2. Main Happy Path Tests (Valid Accounting Flows)
# ==========================================

def test_list_clients_happy_path():
    """Verify retrieval of realistic seed accounting clients (no lorem ipsum)."""
    response = client.get("/api/v1/clients")
    assert response.status_code == 200
    clients = response.json()
    assert len(clients) >= 5

    # Check realistic client details
    company_names = [c["company_name"] for c in clients]
    assert "Apex Advisory Partners LLC" in company_names
    assert "Crestview Logistics UK Ltd" in company_names
    assert "Solaria BioTech Inc." in company_names


def test_get_single_client_happy_path():
    """Verify fetching an existing client profile by client_id."""
    response = client.get("/api/v1/clients/CLI-1001")
    assert response.status_code == 200
    data = response.json()
    assert data["client_id"] == "CLI-1001"
    assert data["company_name"] == "Apex Advisory Partners LLC"
    assert data["tax_identifier"] == "EIN-12-3456789"


def test_create_client_happy_path():
    """Verify onboarding a new corporate accounting client."""
    new_client = {
        "company_name": "Horizon Clean Energy Corp",
        "tax_identifier": "EIN-88-2940192",
        "contact_email": "tax@horizonenergy.com",
        "billing_currency": "USD",
        "credit_limit": 100000.0,
    }
    response = client.post("/api/v1/clients", json=new_client)
    assert response.status_code == 201
    created = response.json()
    assert created["company_name"] == "Horizon Clean Energy Corp"
    assert created["client_id"].startswith("CLI-")
    assert created["status"] == "Active"
    assert created["outstanding_balance"] == 0.0


def test_create_invoice_happy_path():
    """Verify issuing a valid multi-line accounting invoice and tax computation."""
    invoice_payload = {
        "client_id": "CLI-1001",
        "due_date": "2026-12-31",
        "tax_rate": 0.0825,
        "line_items": [
            {
                "description": "Year-End Corporate Financial Statement Preparation",
                "quantity": 30.0,
                "unit_price": 200.0,
            },
            {
                "description": "Internal Controls Assessment & Advisory",
                "quantity": 10.0,
                "unit_price": 250.0,
            },
        ],
        "notes": "Remittance via Fedwire to LedgerPro Operating Account",
    }
    response = client.post("/api/v1/invoices", json=invoice_payload)
    assert response.status_code == 201
    inv = response.json()

    # Subtotal = (30 * 200) + (10 * 250) = 6000 + 2500 = 8500
    assert inv["subtotal"] == 8500.0
    # Tax = 8500 * 0.0825 = 701.25
    assert inv["tax_amount"] == 701.25
    # Total = 8500 + 701.25 = 9201.25
    assert inv["total_amount"] == 9201.25
    assert inv["status"] == "Issued"


def test_record_invoice_payment_happy_path():
    """Verify recording payment on an issued invoice settles status."""
    response = client.post("/api/v1/invoices/INV-2026-002/pay")
    assert response.status_code == 200
    paid_inv = response.json()
    assert paid_inv["status"] == "Paid"


def test_post_balanced_ledger_entry_happy_path():
    """Verify posting a double-entry journal transaction that strictly balances."""
    balanced_entry = {
        "transaction_date": "2026-11-20",
        "reference": "TX-RET-901",
        "description": "Retainer deposit received from Solaria BioTech",
        "lines": [
            {
                "account_code": "1010",
                "account_name": "Operating Cash Account",
                "debit": 15000.0,
                "credit": 0.0,
            },
            {
                "account_code": "2050",
                "account_name": "Unearned Client Retainers",
                "debit": 0.0,
                "credit": 15000.0,
            },
        ],
    }
    response = client.post("/api/v1/ledger/entries", json=balanced_entry)
    assert response.status_code == 201
    entry = response.json()
    assert entry["total_amount"] == 15000.0
    assert entry["entry_id"].startswith("GL-")


def test_get_ledger_summary_happy_path():
    """Verify General Ledger balance calculation."""
    response = client.get("/api/v1/ledger/summary")
    assert response.status_code == 200
    summary = response.json()
    assert summary["is_ledger_balanced"] is True
    assert summary["total_debits_posted"] == summary["total_credits_posted"]
    assert summary["total_journal_entries"] >= 2


# ==========================================
# 3. Failure Path & Input Validation Tests
# ==========================================

def test_client_not_found_failure():
    """Verify requesting a non-existent client returns clear 404 message."""
    response = client.get("/api/v1/clients/CLI-9999")
    assert response.status_code == 404
    data = response.json()
    assert data["status"] == "error"
    assert "CLI-9999" in data["message"]


def test_duplicate_tax_id_conflict_failure():
    """Verify duplicate EIN/Tax ID registration returns 409 Conflict."""
    duplicate_payload = {
        "company_name": "Apex Clone Corp",
        "tax_identifier": "EIN-12-3456789",  # Already belongs to CLI-1001
        "contact_email": "clone@apex.com",
    }
    response = client.post("/api/v1/clients", json=duplicate_payload)
    assert response.status_code == 409
    data = response.json()
    assert data["error_code"] == "HTTP_409"
    assert "already registered" in data["message"]


def test_empty_client_payload_handled_gracefully():
    """Verify sending an empty JSON payload returns 422 with structured errors; doesn't crash."""
    response = client.post("/api/v1/clients", json={})
    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "error"
    assert data["error_code"] == "INPUT_VALIDATION_ERROR"
    assert len(data["details"]) > 0
    # Confirms company_name, tax_identifier, contact_email are reported missing
    fields = [d["field"] for d in data["details"]]
    assert any("company_name" in f for f in fields)
    assert any("tax_identifier" in f for f in fields)


def test_invalid_email_format_failure():
    """Verify malformed email returns 422 validation failure."""
    bad_payload = {
        "company_name": "Valid Name Inc",
        "tax_identifier": "EIN-99-0011223",
        "contact_email": "not-an-email-address",
    }
    response = client.post("/api/v1/clients", json=bad_payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "INPUT_VALIDATION_ERROR"


def test_invoice_creation_nonexistent_client_failure():
    """Verify issuing invoice for non-existent client returns 400 Bad Request."""
    bad_invoice = {
        "client_id": "CLI-NONEXISTENT",
        "due_date": "2026-12-31",
        "line_items": [
            {
                "description": "Tax Filing",
                "quantity": 10.0,
                "unit_price": 100.0,
            }
        ],
    }
    response = client.post("/api/v1/invoices", json=bad_invoice)
    assert response.status_code == 400
    data = response.json()
    assert "does not exist" in data["message"]


def test_invoice_creation_suspended_client_failure():
    """Verify issuing invoice to a Suspended client is blocked with clear error."""
    suspended_invoice = {
        "client_id": "CLI-1005",  # Sterling Financial Trust is Suspended in seed
        "due_date": "2026-12-31",
        "line_items": [
            {
                "description": "Advisory Services",
                "quantity": 5.0,
                "unit_price": 200.0,
            }
        ],
    }
    response = client.post("/api/v1/invoices", json=suspended_invoice)
    assert response.status_code == 400
    assert "suspended" in response.json()["message"].lower()


def test_invoice_negative_quantity_failure():
    """Verify negative quantity or price in invoice lines fails schema validation."""
    invalid_invoice = {
        "client_id": "CLI-1001",
        "due_date": "2026-12-31",
        "line_items": [
            {
                "description": "Audit Hours",
                "quantity": -5.0,  # Negative quantity
                "unit_price": 200.0,
            }
        ],
    }
    response = client.post("/api/v1/invoices", json=invalid_invoice)
    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "INPUT_VALIDATION_ERROR"


def test_unbalanced_ledger_entry_failure():
    """Verify posting an unbalanced double-entry journal is rejected with clear error."""
    unbalanced_entry = {
        "transaction_date": "2026-11-20",
        "reference": "TX-ERR-001",
        "description": "Fraudulent or erroneous unbalanced journal entry",
        "lines": [
            {
                "account_code": "1010",
                "account_name": "Operating Cash Account",
                "debit": 5000.0,
                "credit": 0.0,
            },
            {
                "account_code": "4010",
                "account_name": "Audit Services Revenue",
                "debit": 0.0,
                "credit": 4000.0,  # Missing 1000 credit!
            },
        ],
    }
    response = client.post("/api/v1/ledger/entries", json=unbalanced_entry)
    assert response.status_code == 422
    data = response.json()
    assert "Unbalanced journal entry" in str(data)


def test_double_payment_on_invoice_failure():
    """Verify recording payment on an already paid invoice is rejected with 400."""
    # INV-2026-003 is already Paid in the seed data
    response = client.post("/api/v1/invoices/INV-2026-003/pay")
    assert response.status_code == 400
    data = response.json()
    assert "already marked as Paid" in data["message"]
