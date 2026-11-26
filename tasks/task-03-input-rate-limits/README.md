# Task 3 - LedgerPro Accountants: Input and Rate Limit Tests

Port: **8002** | Tests: **43 passing** | Prerequisite: Task 1 (port 8000) + Task 2 (port 8001)

---

## What This Task Does

This task adds an input validation and rate limiting layer to the LedgerPro Accountants API security
review. Three accounting endpoints (client intake, invoice submission, and ledger posting) are
protected at the schema layer using Pydantic v2. A fixed-window in-process rate limiter rejects
callers who exceed 10 requests per 60-second window.

The 43-test suite covers:
- Happy-path acceptance of realistic accounting payloads
- Boundary value rejection (zero amounts, oversized strings, amounts above a 10 million GBP ceiling)
- SQL injection pattern detection (semicolons, comment sequences, `drop`, `insert`, `select`, `union`)
- XSS / HTML injection detection (`<script>`, `onerror=`, `javascript:`)
- Double-entry bookkeeping rule enforcement (debit XOR credit, neither both nor neither)
- Rate limiter window logic (within limit passes, exceeding limit raises 429 with `retry_after_seconds`)

---

## Directory Layout

```text
task-03-input-rate-limits/
  app/
    __init__.py
    main.py           - FastAPI app, security headers middleware, structured 422 handler
    config.py         - Port, rate limit constants, field length ceilings
    rate_limiter.py   - Fixed-window in-process counter per (IP, endpoint) key
    routes/
      __init__.py
      tests.py        - POST /api/v1/clients, /invoices, /ledger; GET /api/v1/ping
    schemas/
      __init__.py
      inputs.py       - Pydantic v2 models with field validators and injection checks
  tests/
    __init__.py
    test_input_limits.py  - 43 automated tests
  requirements.txt
  pytest.ini
  README.md
```

---

## How to Run

```powershell
cd tasks/task-03-input-rate-limits
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8002 --reload
```

Swagger UI: http://127.0.0.1:8002/docs
Health check: http://127.0.0.1:8002/health

### Run the test suite

```powershell
cd tasks/task-03-input-rate-limits
python -m pytest tests/ -v
```

Expected output: `43 passed`

### Confirm injection detection manually

```powershell
# SQLi attempt - expect 422
curl -s -X POST http://127.0.0.1:8002/api/v1/clients `
  -H "Content-Type: application/json" `
  -d "{\"client_name\": \"' OR 1=1 --\", \"contact_email\": \"a@b.com\", \"annual_revenue\": \"1000\"}"

# XSS attempt - expect 422
curl -s -X POST http://127.0.0.1:8002/api/v1/clients `
  -H "Content-Type: application/json" `
  -d "{\"client_name\": \"Test\", \"contact_email\": \"a@b.com\", \"annual_revenue\": \"1000\", \"description\": \"<script>alert(1)</script>\"}"

# Valid client - expect 200
curl -s -X POST http://127.0.0.1:8002/api/v1/clients `
  -H "Content-Type: application/json" `
  -d "{\"client_name\": \"Crescent Textile Mills Ltd\", \"contact_email\": \"accounts@crescenttextile.pk\", \"annual_revenue\": \"2500000\"}"
```

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Service health check |
| GET | /api/v1/ping | Rate limit probe endpoint |
| POST | /api/v1/clients | Onboard a new accounting client |
| POST | /api/v1/invoices | Raise an invoice against a client |
| POST | /api/v1/ledger | Post a double-entry ledger line |

### Field rules enforced at the schema layer

**POST /api/v1/clients**
- `client_name`: 2-100 chars, no unescaped quotes, no SQL or HTML injection tokens
- `contact_email`: RFC 5321 format, max 254 chars
- `annual_revenue`: 0 to 10,000,000 GBP (Decimal)
- `description`: optional, max 500 chars, injection-checked

**POST /api/v1/invoices**
- `client_id`: matches `^CLI-[0-9]{4}$`
- `invoice_ref`: matches `^INV-[0-9]{4,6}$`
- `amount`: > 0 and <= 10,000,000 GBP
- `line_item`: 3-200 chars, injection-checked

**POST /api/v1/ledger**
- `account_code`: 4-6 digits
- `debit` / `credit`: exactly one must be non-zero (double-entry rule)
- `narrative`: 5-300 chars, injection-checked

---

## Realistic Sample Payloads

```json
// Client intake - LedgerPro onboarding form
{
  "client_name": "Crescent Textile Mills Ltd",
  "contact_email": "accounts@crescenttextile.pk",
  "annual_revenue": "2500000.00",
  "description": "Quarterly VAT and payroll processing"
}

// Invoice
{
  "client_id": "CLI-0042",
  "invoice_ref": "INV-100122",
  "amount": "4800.00",
  "line_item": "Quarterly VAT return preparation - Q3 2026"
}

// Ledger entry
{
  "account_code": "4000",
  "debit": "4800.00",
  "credit": "0",
  "narrative": "Payment received - Crescent Textile Mills Q3 invoice"
}
```

---

## ADR-004: In-Process Fixed-Window Rate Limiter vs. External Rate Limiting

**Decision**: Implement the rate limiter as an in-process module-level counter rather than delegating
to Redis, nginx, or a cloud gateway.

**Reason**: The lab runs as a single-process uvicorn instance. An external dependency (Redis, nginx)
would increase the setup burden for a reviewer who only needs to `pip install -r requirements.txt`
and run pytest. The in-process implementation is deterministic, requires no external services, and
exercises the same logic a real limiter would (counter per key, window reset, 429 response with
`retry_after_seconds`).

**Trade-off**: The in-process counter does not survive a process restart, does not share state across
multiple workers (e.g. gunicorn with four workers), and cannot be managed from a WAF or operations
dashboard. A production deployment of LedgerPro would use a Redis-backed limiter or an API gateway
(AWS API Gateway, nginx-plus, Cloudflare) with the same 10-requests-per-minute policy tuned per
endpoint sensitivity. That migration path is documented so a client reviewer knows the lab decision
is intentional, not an oversight.

**Security note**: Even the in-process limiter correctly returns a 429 with a structured
`retry_after_seconds` field, which is the observable behaviour a penetration test would check.

---

## SEC-FINDING-002: Injection Detection at the Schema Layer Only

**Observation**: Injection pattern detection (SQL tokens, XSS tokens) is applied by Pydantic
validators before the route handler is called. The application layer does not use a database, so
there is no parameterised query to test. In a production system backed by PostgreSQL or MongoDB,
the defence-in-depth order would be: schema validation first, then ORM parameterisation, then a
WAF rule. The schema-layer check here demonstrates the principle; it is not a substitute for
parameterised queries when a real data store is present.

---

## Lab Seed Data

| Client | Email | Annual Revenue |
|--------|-------|---------------|
| Crescent Textile Mills Ltd | accounts@crescenttextile.pk | GBP 2,500,000 |
| Khalid Sons Trading Co | finance@khalidsons.com | GBP 850,000 |
| Pak Agri Exports Ltd | ops@pakagriexports.com | GBP 4,100,000 |

Note: These are lab-only seed credentials and sample values, never used in production.

---

## Test Coverage Summary

| Group | Tests | All Pass |
|-------|-------|----------|
| Health and meta | 4 | yes |
| Client intake - valid | 6 | yes |
| Client intake - invalid | 7 | yes |
| Client intake - injection | 6 | yes |
| Invoice - valid | 3 | yes |
| Invoice - invalid | 6 | yes |
| Ledger entry | 7 | yes |
| Rate limiter | 4 | yes |
| **Total** | **43** | **yes** |
