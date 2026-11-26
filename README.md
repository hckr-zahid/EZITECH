# EZITECH Cybersecurity Internship - LedgerPro Accountants Security Review

[![Track](https://img.shields.io/badge/Track-Cyber%20Security%20(Advanced)-red.svg)](#intern-profile)
[![Client](https://img.shields.io/badge/Client-LedgerPro%20Accountants-blue.svg)](#client-profile)
[![Tasks Completed](https://img.shields.io/badge/Progress-Task%203%2F6%20Complete-green.svg)](#project-roadmap)
[![OWASP API Top 10](https://img.shields.io/badge/Standard-OWASP%20API%20Top%2010-orange.svg)](https://owasp.org/www-project-api-security/)
[![Tests](https://img.shields.io/badge/Automated%20Tests-92%20Passed-brightgreen.svg)](#test-suite)

API security evaluation and hardening portfolio for **LedgerPro Accountants** (an accounting and statutory audit firm). Undertaken as part of the **Ezitech Software House Cybersecurity Internship**, this repository tracks the security review, vulnerability assessment, remediation, and automated CI/CD security pipeline implementation across six milestones.

---

## Engineer and Internship Details

* **Intern / Engineer**: Zahid Ullah
* **Specialization**: Cyber Security (CEH v13, CHFI, ISC2 CC)
* **Organization**: Ezitech Software House
* **Target System**: LedgerPro Accountants Core Accounting and Billing API
* **Project Period**: 30 Days (20 Nov 2026 - 20 Dec 2026)

---

## 6-Task Security Review Roadmap

| # | Task Directory | Milestone and Objective | Estimated Days | Status |
|---|---|---|---|---|
| **01** | [`tasks/task-01-lab-api-setup/`](./tasks/task-01-lab-api-setup/) | **Lab API Setup**: Stand up core accounting API with authentic datasets, input validation, and ADR-001. | 2 Days | Completed |
| **02** | [`tasks/task-02-auth-token-checks/`](./tasks/task-02-auth-token-checks/) | **Authentication and Token Checks**: Implement bcrypt password hashing, JWT lifecycle, RBAC enforcement, and audit token revocation gap (ADR-002, ADR-003). | 7 Days | Completed |
| **03** | [`tasks/task-03-input-rate-limits/`](./tasks/task-03-input-rate-limits/) | **Input and Rate Limit Tests**: Schema-layer injection detection, boundary value enforcement, and fixed-window rate limiting (ADR-004, SEC-FINDING-002). | 6 Days | Completed |
| **04** | `tasks/task-04-security-fixes/` | **Security Fixes**: Remediate discovered vulnerabilities, harden input parsers, and seal token bypasses. | 7 Days | Scheduled |
| **05** | `tasks/task-05-security-tests-ci/` | **Security Tests in CI**: Integrate automated DAST/SAST security gates (Semgrep, Schemathesis, OWASP ZAP) into CI. | 6 Days | Scheduled |
| **06** | `tasks/task-06-report-and-handover/` | **Report and Handover**: Formal executive and technical penetration testing report with remediation verification. | 2 Days | Scheduled |

---

## Repository Architecture

```text
EZITECH/
  .gitignore                                      - Python/IDE gitignore
  README.md                                       - Master repository index (this file)
  tasks/
    task-01-lab-api-setup/                        - Task 1: Core Accounting Lab API (Port 8000)
      app/
        main.py                                   - FastAPI entrypoint, exception handlers, security headers
        config.py                                 - App settings and environment configurations
        schemas/                                  - Pydantic v2 domain models (client, invoice, ledger)
        routes/                                   - Domain REST endpoints (clients, invoices, ledger)
        data/mock_db.py                           - Realistic accounting seed dataset
      tests/test_api.py                           - 18 automated tests (happy paths and failure paths)
      requirements.txt                            - Task 1 dependencies
      README.md                                   - Task 1 report and ADR-001
      submission_note.md                          - Portal submission text
    task-02-auth-token-checks/                    - Task 2: Auth Engine and Token Security (Port 8001)
      app/
        main.py                                   - FastAPI entrypoint and security middleware
        config.py                                 - JWT settings (HS256, 15m access / 8h refresh)
        data/users.py                             - Bcrypt password hashing (cost factor 12) and staff store
        auth/
          jwt_handler.py                          - Token creation (sub, role, jti, exp) and decoding
          dependencies.py                         - get_current_user, get_active_user, require_role
        schemas/auth.py                           - Auth Pydantic models (login, refresh, profile, inspect)
        routes/auth.py                            - /login, /refresh, /me, /inspect, protected resources
      tests/test_auth.py                          - 31 security and RBAC tests (100% passing)
      requirements.txt                            - Task 2 dependencies
      README.md                                   - Task 2 report, ADR-002, and ADR-003
      submission_note.md                          - Portal submission text
    task-03-input-rate-limits/                    - Task 3: Input Validation and Rate Limits (Port 8002)
      app/
        main.py                                   - FastAPI app, security headers, structured 422 handler
        config.py                                 - Rate limit constants, field length ceilings
        rate_limiter.py                           - Fixed-window in-process counter per (IP, endpoint)
        routes/tests.py                           - POST /clients, /invoices, /ledger; GET /ping
        schemas/inputs.py                         - Pydantic v2 models with injection validators
      tests/test_input_limits.py                  - 43 automated tests (happy paths and attack paths)
      requirements.txt                            - Task 3 dependencies
      README.md                                   - Task 3 report, ADR-004, SEC-FINDING-002
```

---

## Quick Start and Verification

### Task 1: Accounting Lab API (Port 8000)
```powershell
cd tasks/task-01-lab-api-setup
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
python -m pytest -v    # 18 tests passing
```
Swagger UI: http://127.0.0.1:8000/docs

### Task 2: Authentication and Token Lab (Port 8001)
```powershell
cd tasks/task-02-auth-token-checks
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
python -m pytest -v    # 31 tests passing
```
Swagger UI: http://127.0.0.1:8001/docs

### Task 3: Input and Rate Limit Tests (Port 8002)
```powershell
cd tasks/task-03-input-rate-limits
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8002 --reload
python -m pytest -v    # 43 tests passing
```
Swagger UI: http://127.0.0.1:8002/docs

---

## Compliance and Verification Summary

* **Realistic Accounting Datasets**: All corporate clients, service codes, and general ledger journal transactions reflect standard accounting workflows.
* **Input Validation and Exception Handling**: Invalid, malformed, boundary, and injection inputs return structured error codes; internal server errors suppress stack trace disclosure.
* **Password Derivation**: Direct bcrypt key derivation with cost factor 12 across all seeded staff accounts.
* **Token Architecture**: RFC 7519 compliant JWTs with 15-minute access lifetimes, 8-hour refresh lifetimes, unique `jti` identifiers, and strict `type` claims.
* **Injection Detection**: SQL and HTML injection patterns are detected at the Pydantic schema layer before route handlers are called (see SEC-FINDING-002 in Task 3 README).
* **Rate Limiting**: Fixed-window counter (10 requests per 60 seconds per IP per endpoint) rejects excess callers with 429 and a `retry_after_seconds` field (see ADR-004 in Task 3 README).
* **Automated Test Coverage**: **92/92 total automated tests passing** (18 in Task 1 + 31 in Task 2 + 43 in Task 3) covering happy paths and failure/attack scenarios.
