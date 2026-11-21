"""
LedgerPro Accountants — Task 2: Authentication & Token Checks
FastAPI entrypoint with security middleware and auth routes.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import APP_VERSION, API_PREFIX
from app.routes.auth import router as auth_router

app = FastAPI(
    title="LedgerPro Accountants — Auth & Token Security Lab",
    description=(
        "Task 2: Authentication and token checks. "
        "Implements JWT-based login, role-based access control (RBAC), "
        "token refresh, and security audit inspection endpoints. "
        "Built on top of the Task 1 Lab API for progressive security review."
    ),
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Server"] = "LedgerPro-Lab-Engine"
    # Prevent browsers from caching auth responses
    if "/auth/" in request.url.path:
        response.headers["Cache-Control"] = "no-store"
        response.headers["Pragma"] = "no-cache"
    return response


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    errors = [
        {"field": " -> ".join(str(l) for l in e.get("loc", [])), "message": e.get("msg"), "type": e.get("type")}
        for e in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"status": "error", "error_code": "INPUT_VALIDATION_ERROR", "details": errors,
                 "timestamp": datetime.now(timezone.utc).isoformat()},
    )


@app.exception_handler(StarletteHTTPException)
async def http_exc_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "error_code": f"HTTP_{exc.status_code}",
                 "message": exc.detail, "timestamp": datetime.now(timezone.utc).isoformat()},
    )


@app.exception_handler(Exception)
async def global_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"status": "error", "error_code": "INTERNAL_SERVER_ERROR",
                 "message": "An internal error occurred. No sensitive details disclosed.",
                 "timestamp": datetime.now(timezone.utc).isoformat()},
    )


@app.get("/", tags=["System"])
def root():
    return {"service": "LedgerPro Auth & Token Security Lab", "version": APP_VERSION, "docs": "/docs"}


@app.get("/health", tags=["System"])
def health():
    return {"status": "healthy", "version": APP_VERSION, "timestamp": datetime.now(timezone.utc).isoformat()}


app.include_router(auth_router, prefix=API_PREFIX)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8001, reload=True)
