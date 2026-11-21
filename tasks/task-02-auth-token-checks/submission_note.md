# Task 2 Submission Note: Authentication & Token Checks

**Project**: LedgerPro Accountants API Security Review  
**Intern**: Zahid Ullah (CEH v13, CHFI, ISC² CC)  
**Portal**: Ezitech Software House (`portal.ezitech.org`)  
**Task**: Task 2 — Authentication and Token Checks  
**Repository**: `https://github.com/hckr-zahid/EZITECH` (Branch: `main`)

---

## Executive Summary

Task 2 has been successfully completed in accordance with all specifications outlined in the Task 2 Project Brief. 

A production-grade, cryptographically secure authentication framework has been built for LedgerPro Accountants, featuring:
1. **Bcrypt Password Security**: Passwords salted and hashed with 12 rounds of bcrypt; plaintext secrets are eliminated across the system.
2. **RFC 7519 Compliant JWT Architecture**: Tokens signed with HS256, carrying standard and custom claims (`sub`, `role`, `iat`, `exp`, `jti`, and `type`).
3. **Hierarchical RBAC**: Strict multi-tiered access control enforcing permission separation across 4 distinct accounting firm roles (`admin`, `auditor`, `accountant`, `viewer`).
4. **Token Lifecycle & Refresh Mechanism**: Separation of short-lived access tokens (15 minutes) and long-lived refresh tokens (8 hours).
5. **Defenses Against Common Web & API Attacks**:
   - Prevention of user enumeration via uniform 401 messaging and response timing.
   - Protection against token type confusion by validating token type (`type: access` vs `type: refresh`).
   - Prevention of token reuse/replay through unique UUIDv4 token IDs (`jti`).
   - Hardened HTTP headers (`Cache-Control: no-store`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`).
   - Immediate blocking of deactivated/off-boarded accounts (`403 Forbidden`).
6. **Architecture Decision Record (ADR-002)**: Fully documented justification for HS256 selection versus asymmetric RS256, detailing security boundaries and trade-offs.

---

## Verification & Test Results

A test suite of 31 automated tests was authored and executed locally using `pytest`:

```
======================= 31 passed, 3 warnings in 10.75s =======================
```

All 31 tests pass with zero errors, validating both the primary operational paths and all edge/failure attack scenarios.
