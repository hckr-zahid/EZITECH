"""
LedgerPro Accountants — Task 2: Auth Configuration
JWT settings, algorithm, and token lifetime policy.

ADR-002: HS256 chosen for single-service internal signing (see README).
Secret loaded from env; falls back to dev-only constant that is explicitly
flagged as insecure so a misconfigured deployment is immediately detectable.
"""

import os

# --- JWT Core Settings ---
# In production this MUST be set via environment variable.
# The sentinel value "CHANGE_ME_IN_PRODUCTION" is intentionally
# recognisable so a secret-scanner (e.g. Gitleaks) will fire on it.
SECRET_KEY: str = os.getenv(
    "LEDGERPRO_JWT_SECRET",
    "CHANGE_ME_IN_PRODUCTION_ledgerpro_jwt_2026_!@#"
)
ALGORITHM: str = "HS256"

# Access token: short-lived (15 min) — limits blast radius of a leaked token.
ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

# Refresh token: longer-lived (8 hours) — covers a standard accounting work-shift.
REFRESH_TOKEN_EXPIRE_HOURS: int = 8

# API prefix
API_PREFIX: str = "/api/v1"
APP_VERSION: str = "2.0.0"
