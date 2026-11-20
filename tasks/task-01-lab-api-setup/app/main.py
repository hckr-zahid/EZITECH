"""
LedgerPro Accountants - Lab API Entrypoint
FastAPI core application with custom exception handling, security headers, and domain routes.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

# Ensure project root (task-01-lab-api-setup) is in sys.path regardless of execution working directory
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.routes import clients_router, invoices_router, ledger_router
from app.data.mock_db import db

app = FastAPI(
    title="LedgerPro Accountants - Security Lab API",
    description=(
        "Production-grade Lab API simulating the core accounting, client management, "
        "and general ledger backend for LedgerPro Accountants. "
        "Engineered for API Security Audits, Authentication Testing, and Vulnerability Assessment."
    ),
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS middleware configured for development/lab environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Server"] = "LedgerPro-Lab-Engine"
    return response


# Custom Error Handler: Schema & Input Validation Failures (HTTP 422)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error.get("loc", []))
        errors.append({
            "field": field,
            "message": error.get("msg"),
            "type": error.get("type"),
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "error_code": "INPUT_VALIDATION_ERROR",
            "message": "The submitted payload contains missing, malformed, or invalid fields.",
            "details": errors,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


# Custom Error Handler: Standard HTTP Exceptions
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "error_code": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


# Global Crash-Prevention Handler (HTTP 500) - Eliminates Stack Trace Leakage
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An internal error occurred while processing the accounting transaction. Operation aborted safely.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


# Root and System Health Endpoints
@app.get("/", tags=["System Information"])
def root():
    return {
        "service": "LedgerPro Accountants API",
        "status": "Operational",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["System Information"])
def health_check():
    return {
        "status": "healthy",
        "environment": settings.environment,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": "in_memory_thread_safe_active",
        "version": settings.app_version,
    }


# Admin / Testing state reset endpoint
@app.post(f"{settings.api_prefix}/admin/reset", tags=["Lab Admin & Testing"])
def reset_database():
    """Resets the mock accounting database back to seed state for clean test isolation."""
    db.reset()
    return {
        "status": "success",
        "message": "LedgerPro accounting database reset to baseline seed state.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# Include Domain Routers
app.include_router(clients_router, prefix=settings.api_prefix)
app.include_router(invoices_router, prefix=settings.api_prefix)
app.include_router(ledger_router, prefix=settings.api_prefix)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
