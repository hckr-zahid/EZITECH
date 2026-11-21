# Task 2: Authentication & Token Security Checks

**Component**: LedgerPro Accountants — API Security Review Lab (Task 2)  
**Author**: Zahid Ullah (CEH v13, CHFI, ISC² CC)  
**Organization**: Ezitech Software House (`portal.ezitech.org`)  
**Service Port**: `8001` (coexists with Task 1 on `8000`)

---

## 1. Overview & Architecture

Task 2 implements a robust, production-grade authentication and token validation layer for LedgerPro Accountants. Built on top of the financial domain logic established in Task 1, this task introduces:

1. **State-of-the-Art Password Hashing**: Passwords are saved and verified using direct `bcrypt` key derivation with 12 rounds of salt. Plaintext passwords are never persisted.
2. **RFC 7519 Compliant JSON Web Tokens (JWT)**: Cryptographically signed tokens utilizing `HS256`, containing subject identity, role claims, timestamp claims (`iat`, `exp`), unique token identifiers (`jti`), and strict token type declarations (`type: access` vs `type: refresh`).
3. **Role-Based Access Control (RBAC)**: Hierarchical access governance granting tiered privileges across firm personnel (`admin` > `auditor` > `accountant` > `viewer`).
4. **Token Lifecycle Management**: Short-lived access tokens (15 minutes) paired with longer-lived refresh tokens (8 hours).
5. **Security Audit & Token Inspector**: Diagnostic inspection endpoints allowing security engineers to analyze token validity, claim payloads, signature status, and remaining time-to-live (TTL).

---

## 2. Realistic Staff Credentials & Role Hierarchy

In accordance with LedgerPro Accountants' operational structure, 5 realistic staff accounts are seeded:

| Username | Full Name | Department | Role | Default Password | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `fatima.zahra` | Fatima Zahra | Administration | **admin** | `FatimaSecure#2026` | Active |
| `tariq.mahmood` | Tariq Mahmood | Statutory Audit & Assurance | **auditor** | `TariqAudit@2026` | Active |
| `zainab.ali` | Zainab Ali | Tax Compliance & Advisory | **accountant** | `ZainabTax!2026` | Active |
| `bilal.khan` | Bilal Khan | Client Relations | **viewer** | `BilalView@2026` | Active |
| `khalid.mansoor`| Khalid Mansoor | Former Employee | **accountant** | `OldPass#2024` | **Deactivated** |

### Role Privilege Matrix

```
       [admin] (Fatima Zahra)
          │  Full access to all accounting data, ledgers, & management
          ▼
      [auditor] (Tariq Mahmood)
          │  Access to ledgers, client audits, and financial compliance
          ▼
     [accountant] (Zainab Ali)
          │  Access to client invoicing, billing records, and tax filings
          ▼
       [viewer] (Bilal Khan)
             Read-only access to basic public rates and non-sensitive data
```

---

## 3. Architecture Decision Record (ADR-002)

### Decision: Selection of JWT Signing Algorithm — HS256 vs RS256

* **Status**: Accepted
* **Context**: The LedgerPro API requires stateless, cryptographically verifiable bearer tokens for authenticating requests. We evaluated two primary signing architectures:
  1. **HS256 (HMAC with SHA-256)**: Symmetric algorithm where the same secret key is used to sign and verify tokens.
  2. **RS256 (RSA Signature with SHA-256)**: Asymmetric algorithm using a private key for signing and a public key for verification.

* **Decision**: **HS256** was selected for the current monolithic lab service deployment.

* **Rationale & Trade-offs**:
  * **Simplicity & Performance**: HS256 has minimal computational overhead compared to asymmetric RSA math, resulting in significantly lower latency per API call during token issuance and validation.
  * **Single Authority**: The LedgerPro core engine currently functions as both the Token Issuer (IdP) and Resource Server. Secret sharing across multiple distinct parties is not required.
  * **Trade-off / Future Evolution**: In a distributed microservices architecture (where third-party services or separated reporting microservices need to verify tokens without being trusted to sign them), HS256 poses the risk that any service verifying tokens could forge them. Once LedgerPro splits into distributed services, migration to **RS256** or **EdDSA (Ed25519)** will be recommended.

---

## 4. Key Security Controls & Defenses Implemented

### 1. Username Enumeration Prevention
* **Vulnerability Mitigated**: OWASP Top 10 API3:2023 — Broken Object Property Level Authorization / Identification.
* **Implementation**: Whether a client provides an invalid username or a wrong password, the endpoint returns an identical `401 Unauthorized` response with the uniform message: `Invalid username or password`. No timing or descriptive differentiation is exposed to attackers attempting to harvest usernames.

### 2. Token Type Confusion Defense
* **Vulnerability Mitigated**: Flawed token usage where a long-lived refresh token is presented directly to access-protected resource endpoints.
* **Implementation**: Tokens strictly embed a `"type"` claim (`"access"` vs `"refresh"`). Dependency injectors verify that incoming Bearer tokens explicitly bear `"type": "access"`, rejecting refresh tokens with a `401 Unauthorized` before processing any business logic.

### 3. Immediate Account Deactivation Enforcement
* **Vulnerability Mitigated**: Zombie session abuse and off-boarded staff access.
* **Implementation**: Deactivated accounts (`disabled: True`) are rejected immediately during authentication with `403 Forbidden`, regardless of whether the submitted password matches.

### 4. Replay Attack & Collision Mitigation (`jti`)
* **Implementation**: Every token generated receives a cryptographically unique `jti` (JWT ID) via UUIDv4. This prevents token collisions and enables downstream token revocation blacklisting.

### 5. HTTP Response Caching Hardening
* **Implementation**: All responses passing through `/auth/` routes automatically include `Cache-Control: no-store` and `Pragma: no-cache` headers, ensuring sensitive authentication payloads and tokens are never cached by intermediary proxies or browser caches.

---

## 5. API Endpoints Reference

### Authentication Routes (`/api/v1/auth`)

| Method | Endpoint | Access Level | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/login` | Public | Authenticates credentials and issues access & refresh tokens |
| `POST` | `/api/v1/auth/refresh` | Public (Requires valid Refresh Token) | Exchanges valid refresh token for a newly issued access token |
| `GET` | `/api/v1/auth/me` | Authenticated (Any Role) | Returns the authenticated user's profile and assigned role |
| `POST` | `/api/v1/auth/inspect` | Public (Security Audit Tool) | Decodes token and inspects claim structure, validity, & TTL |

### Protected Resource Routes (`/api/v1/auth/resources`)

| Method | Endpoint | Required Role | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/auth/resources/ledger-report` | `auditor` or higher (`admin`) | Confidential general ledger financial report |
| `GET` | `/api/v1/auth/resources/client-list` | `accountant` or higher | Full corporate client roster and billing profiles |
| `GET` | `/api/v1/auth/resources/public-rates` | `viewer` or higher (All active staff) | Public standard billing rates |

---

## 6. How to Run & Verify

### Prerequisites
* Python 3.10+
* Dependencies:
  ```bash
  pip install -r requirements.txt
  ```

### Running the API Server
Start the Uvicorn server on port `8001`:
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```
Interactive API documentation is accessible at:
* Swagger UI: `http://127.0.0.1:8001/docs`
* ReDoc: `http://127.0.0.1:8001/redoc`

### Executing the Test Suite
Run the 31 comprehensive security and functional test cases:
```bash
python -m pytest -v
```
All 31 tests validate:
* Health checks and security headers
* Login happy paths for all 4 roles
* User profile extraction (`/me`)
* Token refresh mechanics
* Role-based access control (RBAC) authorization paths
* Authentication failure handling (invalid credentials, missing tokens, malformed headers, expired tokens, tampered signatures, type confusion)
* Account deactivation enforcement
* Token inspection and TTL reporting
