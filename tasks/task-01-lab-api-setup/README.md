# 🏢 Task 1: Lab API Setup - LedgerPro Accountants

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2.6+-E92063.svg?logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![Pytest](https://img.shields.io/badge/Pytest-18%20Passed-brightgreen.svg?logo=pytest&logoColor=white)](https://docs.pytest.org/)
[![Security Headers](https://img.shields.io/badge/OWASP-Security%20Headers%20Active-blue.svg)](https://owasp.org)

## 📌 Executive Summary
This laboratory environment establishes the target core accounting backend for **LedgerPro Accountants** (a public accounting and audit firm). Built as the foundation for a 6-task security review, it provides a realistic, testable, and robust REST API that simulates real-world client onboarding, professional service billing, and double-entry General Ledger bookkeeping.

---

## 🏛️ Business Domain & Realistic Datasets
In accordance with professional accounting firm operations, all data entities and seed records utilize authentic commercial profiles with **zero *lorem ipsum***:

* **Corporate Accounting Clients**: Real entities with genuine tax identifications (`EIN-12-3456789`, `VAT-GB987654321`), credit ceilings, and billing currencies:
  * `Apex Advisory Partners LLC` (Active, $75,000 credit line)
  * `Crestview Logistics UK Ltd` (Active, £120,000 credit line)
  * `Solaria BioTech Inc.` (Under Audit, $50,000 credit line)
  * `Vanguard Retail Holdings` (Active, $150,000 credit line)
  * `Sterling Financial Trust` (Suspended, risk containment state)
* **Itemized Accounting Services**:
  * Statutory Financial Audit & Assurance Services ($225/hr)
  * Corporate Tax Compliance & IRS Form 1120 Preparation ($245/hr)
  * R&D Tax Credit Calculation & Section 41 Substantiation ($275/hr)
  * Fractional CFO Advisory & Multi-Entity Ledger Reconciliation
* **General Ledger (GL) & Double-Entry Bookkeeping**:
  * Compliant with standard charts of accounts: Assets (`1010 Operating Cash`, `1200 Accounts Receivable`), Liabilities (`2200 Tax Payable`), Revenue (`4010 Audit Revenue`).
  * Enforces the fundamental accounting balance equation: $\sum \text{Debits} \equiv \sum \text{Credits}$.

---

## 🛡️ Input Validation & Crash Prevention
To ensure robust security and prevent unhandled server failures:
1. **Strict Pydantic Schema Validation**: Every endpoint enforces strict types, non-empty text, email formats, and positive quantities ($> 0$).
2. **Normalized Error Schemas**: All invalid or empty payloads trigger structured `422 Unprocessable Content` responses detailing the affected fields.
3. **Global Crash Prevention Middleware**: Catch-all exception handling guarantees that internal errors return controlled `500 Internal Server Error` responses, completely eliminating stack trace and environment leakage.
4. **Security Headers Injected**:
   * `X-Content-Type-Options: nosniff`
   * `X-Frame-Options: DENY`
   * `X-XSS-Protection: 1; mode=block`
   * `Server: LedgerPro-Lab-Engine` (masked server fingerprinting)

---

## ⚖️ Architectural Decision Record (ADR)

### ADR-001: Thread-Safe In-Memory Domain Repository vs. Persistent Database
* **Status**: Accepted
* **Context**: The Lab API must serve as the primary security testing target across Tasks 1-6 (fuzzing, authentication testing, rate-limiting, injection payloads, and automated CI/CD scans).
* **Decision**: Implement an in-memory, thread-safe data store protected by re-entrant mutex locks (`threading.Lock`), coupled with an administrative state-reset endpoint (`POST /api/v1/admin/reset`).
* **Trade-off Analysis**:
  * **Advantages**:
    1. *Zero External Friction*: No external database service (PostgreSQL/MySQL) setup or credential management needed for security testing.
    2. *Deterministic Test Isolation*: Tests can reset the state back to clean baseline seed in under 5 milliseconds, avoiding cross-test state pollution during destructive attack simulations.
    3. *High Throughput*: Enables extreme velocity for automated fuzzing, rate-limit testing, and rapid CI pipeline execution.
  * **Disadvantages**:
    1. *Ephemeral Storage*: State is not persisted across server restarts; changes are volatile.
    2. *Single-Node Scope*: Cannot scale horizontally across multiple stateless worker processes without external state sync.
  * **Mitigation**: A dedicated seed generator re-hydrates authentic records upon each startup and test execution cycle.

---

## 🚀 How to Run and Verify the Lab API

### 1. Prerequisites
* Python 3.10+
* Virtual environment (optional but recommended)

### 2. Installation
```powershell
# Navigate to the task directory
cd "EZITECH/tasks/task-01-lab-api-setup"

# Install dependencies
python -m pip install -r requirements.txt
```

### 3. Start the API Server
```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
* Interactive Swagger Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* Alternative ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
* Health Endpoint: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### 4. Run Automated Test Suite
Execute the full Pytest test suite covering both happy and failure paths:
```powershell
python -m pytest -v
```

---

## 🧪 Test Coverage Breakdown

The test suite in [`tests/test_api.py`](./tests/test_api.py) executes 18 automated tests:

| Test Case | Type | Expected Result | Description |
|---|---|---|---|
| `test_health_check_endpoint` | System | 200 OK | Confirms operational status and metadata |
| `test_security_headers_enforced` | Security | Headers verified | Asserts `X-Frame-Options` and `nosniff` headers |
| `test_list_clients_happy_path` | Happy Path | 200 OK | Verifies retrieval of authentic client accounts |
| `test_get_single_client_happy_path` | Happy Path | 200 OK | Fetches client `CLI-1001` with realistic fields |
| `test_create_client_happy_path` | Happy Path | 201 Created | Registers new corporate entity |
| `test_create_invoice_happy_path` | Happy Path | 201 Created | Computes line items, subtotal, and tax |
| `test_record_invoice_payment_happy_path` | Happy Path | 200 OK | Marks invoice paid and adjusts balance |
| `test_post_balanced_ledger_entry_happy_path`| Happy Path | 201 Created | Posts double-entry journal (Debits == Credits) |
| `test_get_ledger_summary_happy_path` | Happy Path | 200 OK | Asserts general ledger is in balance |
| `test_client_not_found_failure` | Failure Path | 404 Not Found | Requests non-existent client `CLI-9999` |
| `test_duplicate_tax_id_conflict_failure` | Failure Path | 409 Conflict | Rejects duplicate tax registration |
| `test_empty_client_payload_handled_gracefully`| Failure Path | 422 Unprocessable | Empty JSON body returns structured errors |
| `test_invalid_email_format_failure` | Failure Path | 422 Unprocessable | Rejects malformed contact email |
| `test_invoice_creation_nonexistent_client_failure`| Failure Path | 400 Bad Request | Prevents invoice creation without client |
| `test_invoice_creation_suspended_client_failure`| Failure Path | 400 Bad Request | Blocks invoicing for suspended clients |
| `test_invoice_negative_quantity_failure` | Failure Path | 422 Unprocessable | Rejects negative billed quantities |
| `test_unbalanced_ledger_entry_failure` | Failure Path | 422 Unprocessable | Rejects unbalanced double-entry transactions |
| `test_double_payment_on_invoice_failure` | Failure Path | 400 Bad Request | Prevents double settlement on paid invoice |
