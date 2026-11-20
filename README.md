# 🛡️ EZITECH Cybersecurity Internship — LedgerPro Accountants Security Review

[![Track](https://img.shields.io/badge/Track-Cyber%20Security%20(Advanced)-red.svg)](#intern-profile)
[![Client](https://img.shields.io/badge/Client-LedgerPro%20Accountants-blue.svg)](#client-profile)
[![Tasks Completed](https://img.shields.io/badge/Progress-Task%201%2F6%20Complete-green.svg)](#project-roadmap)
[![OWASP API Top 10](https://img.shields.io/badge/Standard-OWASP%20API%20Top%2010-orange.svg)](https://owasp.org/www-project-api-security/)
[![Tests](https://img.shields.io/badge/Automated%20Tests-18%20Passed-brightgreen.svg)](#test-suite)

Production-grade API security evaluation and hardening portfolio for **LedgerPro Accountants** (an accounting and statutory audit firm). Undertaken as part of the **Ezitech Software House Cybersecurity Internship**, this repository tracks the iterative security review, vulnerability assessment, remediation, and automated CI/CD security pipeline implementation across six distinct project milestones.

---

## 👨‍💻 Engineer & Internship Details

* **Intern / Engineer**: Zahid Ullah
* **Specialization**: Cyber Security (CEH v13, CHFI, ISC² CC)
* **Organization**: Ezitech Software House
* **Target System**: LedgerPro Accountants Core Accounting & Billing API
* **Project Period**: 30 Days (20 Nov 2026 – 20 Dec 2026)

---

## 🗺️ 6-Task Security Review Roadmap

| # | Task Directory | Milestone & Objective | Estimated Days | Status |
|---|---|---|---|---|
| **01** | [`tasks/task-01-lab-api-setup/`](./tasks/task-01-lab-api-setup/) | **Lab API Setup**: Stand up core accounting API with authentic datasets, robust input handling, and ADR. | 2 Days | ✅ **Completed** |
| **02** | `tasks/task-02-auth-token-checks/` | **Authentication & Token Checks**: Audit JWT signing, token lifetimes, replay risks, and RBAC / BOLA. | 7 Days | ⏳ Next Up |
| **03** | `tasks/task-03-input-rate-limits/` | **Input & Rate Limit Tests**: Fuzzing, SQLi / NoSQLi probing, payload limits, and DoS rate limit tests. | 6 Days | 🗓️ Scheduled |
| **04** | `tasks/task-04-security-fixes/` | **Security Fixes**: Remediate discovered vulnerabilities, harden input parsers, and seal token bypasses. | 7 Days | 🗓️ Scheduled |
| **05** | `tasks/task-05-security-tests-ci/` | **Security Tests in CI**: Integrate automated DAST/SAST security gates (Semgrep, Schemathesis, OWASP ZAP) into CI. | 6 Days | 🗓️ Scheduled |
| **06** | `tasks/task-06-report-and-handover/` | **Report & Handover**: Formal executive and technical penetration testing report with remediation verification. | 2 Days | 🗓️ Scheduled |

---

## 🏛️ Repository Architecture

```text
EZITECH/
├── .gitignore                                      # Production Python/IDE gitignore
├── README.md                                       # Master repository index (this file)
└── tasks/
    └── task-01-lab-api-setup/                      # Task 1: Complete Lab API Setup
        ├── app/
        │   ├── __init__.py
        │   ├── main.py                             # FastAPI entrypoint, exception handlers, security headers
        │   ├── config.py                           # App settings & environment configurations
        │   ├── schemas/                            # Pydantic v2 domain models
        │   │   ├── __init__.py
        │   │   ├── client.py                       # Client profiles & tax validation
        │   │   ├── invoice.py                      # Multi-line invoice calculation & status
        │   │   └── ledger.py                       # Double-entry General Ledger balancing rules
        │   ├── routes/                             # Domain REST endpoints
        │   │   ├── __init__.py
        │   │   ├── clients.py
        │   │   ├── invoices.py
        │   │   └── ledger.py
        │   └── data/
        │       └── mock_db.py                      # Realistic accounting seed dataset (zero lorem ipsum)
        ├── tests/
        │   ├── __init__.py
        │   └── test_api.py                         # 18 automated tests (happy paths & failure paths)
        ├── requirements.txt                        # Task dependencies
        ├── README.md                               # Detailed task report & Architectural Decision Record (ADR)
        └── submission_note.md                      # Portal submission text
```

---

## ⚡ Quick Start: Running Task 1

```powershell
# 1. Clone repository & enter Task 1 directory
cd tasks/task-01-lab-api-setup

# 2. Install dependencies
python -m pip install -r requirements.txt

# 3. Launch API server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# 4. Run automated test suite
python -m pytest -v
```

* **Interactive API Documentation (Swagger)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **System Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 📜 Compliance & Verification
* **Data Realism**: All corporate clients, service codes, and general ledger journal transactions reflect standard CPA accounting workflows.
* **Fault Tolerance**: All invalid, malformed, or boundary inputs return structured `422` or `400` error codes; global crash prevention eliminates stack trace disclosure.
* **Test Verification**: 18/18 test cases passing with sub-second execution.
