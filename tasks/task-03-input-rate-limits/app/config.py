"""
Task 3 - LedgerPro Accountants: Input and Rate Limit Tests
Configuration settings.
"""

APP_TITLE = "LedgerPro Accountants - Input & Rate Limit Tests"
APP_VERSION = "1.0.0"
APP_PORT = 8002

# Rate limit: max requests per minute per client IP for mutable endpoints.
# Trade-off documented in README ADR-004.
RATE_LIMIT_REQUESTS = 10
RATE_LIMIT_WINDOW_SECONDS = 60

# Maximum allowed field lengths (characters).
MAX_CLIENT_NAME_LEN = 100
MAX_DESCRIPTION_LEN = 500
MAX_EMAIL_LEN = 254   # RFC 5321

# Maximum numeric values for accounting fields.
MAX_INVOICE_AMOUNT = 10_000_000  # 10 million GBP ceiling for sanity check
