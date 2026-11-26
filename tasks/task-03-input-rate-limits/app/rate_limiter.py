"""
Task 3 - LedgerPro Accountants: Input and Rate Limit Tests
In-process rate limiter using a fixed-window counter per (IP, endpoint) key.

Design note: a production deployment would use Redis or nginx-level limiting.
Here we use a module-level dict so the limiter works in-process during tests
without an external dependency.  See README ADR-004 for the full trade-off.
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import DefaultDict, Tuple

from fastapi import Request, HTTPException

from app.config import RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW_SECONDS


# key -> (window_start, hit_count)
_windows: DefaultDict[str, Tuple[float, int]] = defaultdict(lambda: (0.0, 0))


def reset_all() -> None:
    """Clear all counters.  Called by tests between cases."""
    _windows.clear()


def check_rate_limit(request: Request, endpoint: str = "default") -> None:
    """
    Raise 429 if the caller has exceeded RATE_LIMIT_REQUESTS in the current
    window.  Call this from route handlers that must be rate-limited.
    """
    client_ip = request.client.host if request.client else "testclient"
    key = f"{client_ip}:{endpoint}"
    now = time.monotonic()
    window_start, count = _windows[key]

    if now - window_start >= RATE_LIMIT_WINDOW_SECONDS:
        # Start a fresh window
        _windows[key] = (now, 1)
        return

    if count >= RATE_LIMIT_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "rate_limit_exceeded",
                "message": (
                    f"Too many requests. Limit is {RATE_LIMIT_REQUESTS} per "
                    f"{RATE_LIMIT_WINDOW_SECONDS} seconds."
                ),
                "retry_after_seconds": int(
                    RATE_LIMIT_WINDOW_SECONDS - (now - window_start)
                ),
            },
        )

    _windows[key] = (window_start, count + 1)
