# 📝 Task 1 Submission Note: Lab API Setup — LedgerPro Accountants

**Student / Intern**: Zahid Ullah  
**Technology**: Cyber Security (Advanced)  
**Client**: LedgerPro Accountants  
**Task**: Task 1 — Lab API Setup (2 Days)  

---

### What Was Done
1. **Engineered the Core Accounting Lab API**:
   - Built a high-performance REST API using **FastAPI** and **Pydantic v2** modeling the operations of LedgerPro Accountants.
   - Implemented three core business domains:
     - **Client Management**: Onboarding, corporate tax IDs, credit limits, account statuses (`Active`, `Suspended`, `Under_Audit`).
     - **Invoicing & Billing**: Line-item calculations, service rates, automated tax rate computations, and payment settlement.
     - **General Ledger (GL)**: Double-entry bookkeeping enforcing standard chart of accounts (`1010 Operating Cash`, `1200 Accounts Receivable`, `4010 Audit Revenue`) and balanced transactions ($\sum \text{Debits} == \sum \text{Credits}$).
2. **Curated Authentic Accounting Data**:
   - Seeded the system with authentic business records (e.g., *Apex Advisory Partners LLC*, *Crestview Logistics UK Ltd*, *Solaria BioTech Inc.*) and genuine service line items (Statutory Audits, Corporate Tax 1120 Filings, R&D Tax Credit Section 41). Zero *lorem ipsum* was used.
3. **Hardened Input Validation & Error Handling**:
   - Configured custom validation handlers to catch empty, malformed, or hostile inputs, returning structured `422` and `400` status codes.
   - Implemented a global exception barrier to prevent application crashes and eliminate stack trace disclosure (OWASP API Security).
   - Injected security headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`).
4. **Developed Automated Test Suite (`pytest`)**:
   - Created 18 automated test cases in `tests/test_api.py` covering all primary happy paths, edge cases, and failure scenarios. All 18 tests pass in ~1.2s.
5. **Documented Architectural Decision Record (ADR)**:
   - Evaluated the architectural decision of an in-memory thread-safe repository with deterministic reset capabilities vs. an external database, detailing trade-offs for security auditing and fuzzing.

### Why It Was Done
- **Senior-Level Engineering Quality**: In an accounting firm, integrity and precision of financial records are paramount. Building strict schema validation and double-entry consistency upfront ensures the platform models a real client's architecture.
- **Foundation for Subsequent Security Tasks**: Tasks 2 through 6 will systematically assess authentication, token handling, input fuzzing, rate limiting, and CI/CD security automation. Having a reliable, reproducible, and crash-proof lab API with deterministic state reset makes subsequent attack simulations and remediation verification seamless.
