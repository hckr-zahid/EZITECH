"""
Task 3 - LedgerPro Accountants: Input and Rate Limit Tests
FastAPI application entry point - port 8002.
"""

from __future__ import annotations

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config import APP_TITLE, APP_VERSION
from app.routes.tests import router

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description=(
        "Task 3 of the LedgerPro Accountants API security review. "
        "Demonstrates Pydantic v2 input validation, injection detection, "
        "and a fixed-window rate limiter for mutable endpoints."
    ),
)

# ---------------------------------------------------------------------------
# Security headers on every response
# ---------------------------------------------------------------------------

@app.middleware("http")
async def add_security_headers(request: Request, call_next: callable) -> Response:
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Cache-Control"] = "no-store"
    return response


# ---------------------------------------------------------------------------
# Structured 422 error body (Pydantic validation failures)
# ---------------------------------------------------------------------------

@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = []
    for err in exc.errors():
        errors.append({
            "field": " -> ".join(str(loc) for loc in err["loc"]),
            "message": err["msg"],
            "input": err.get("input"),
        })
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_failed",
            "detail": errors,
        },
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

app.include_router(router)


@app.get("/health", tags=["meta"])
async def health() -> dict:
    return {"status": "ok", "task": "03", "port": 8002}
