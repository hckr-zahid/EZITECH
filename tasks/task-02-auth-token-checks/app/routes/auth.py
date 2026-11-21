"""
LedgerPro Accountants - Task 2: Authentication Routes
Covers: Login, Refresh, Logout (token invalidation note), Me, Token Inspect.
"""

from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError, ExpiredSignatureError
from jose import jwt as jose_jwt

from app.auth.jwt_handler import create_access_token, create_refresh_token, decode_token
from app.auth.dependencies import get_active_user, require_role
from app.data.users import authenticate_user, get_user
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest, UserProfile, TokenInspectResponse
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/auth", tags=["Authentication & Token Management"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Staff Login - Issue JWT access + refresh tokens",
    description=(
        "Authenticates LedgerPro staff credentials. Returns a short-lived access token "
        "(15 min) and long-lived refresh token (8 hours). "
        "Disabled accounts are blocked regardless of correct password."
    ),
)
def login(payload: LoginRequest):
    user = authenticate_user(payload.username, payload.password)
    if not user:
        # Return identical message for wrong username OR wrong password
        # to prevent username enumeration (OWASP API Security - Broken Authentication)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Username or password is incorrect.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.get("disabled"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Contact LedgerPro IT administration.",
        )

    token_data = {"sub": user["username"], "role": user["role"]}
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in_seconds=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        role=user["role"],
        username=user["username"],
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh - Exchange a valid refresh token for a new access token",
    description=(
        "Validates the supplied refresh token (checks signature, expiry, and type claim). "
        "Issues a fresh access token. Rejects access tokens supplied here - type must be 'refresh'."
    ),
)
def refresh_token(payload: RefreshRequest):
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Refresh token is invalid, expired, or of wrong type.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        claims = decode_token(payload.refresh_token)
        if claims.get("type") != "refresh":
            raise credentials_exc
        username = claims.get("sub")
        if not username:
            raise credentials_exc
    except JWTError:
        raise credentials_exc

    user = get_user(username)
    if not user or user.get("disabled"):
        raise credentials_exc

    token_data = {"sub": username, "role": user["role"]}
    new_access = create_access_token(data=token_data)
    new_refresh = create_refresh_token(data=token_data)

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        token_type="bearer",
        expires_in_seconds=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        role=user["role"],
        username=username,
    )


@router.get(
    "/me",
    response_model=UserProfile,
    summary="Current User - Return authenticated staff profile",
    description="Returns the profile of the currently authenticated staff member. Requires valid access token.",
)
def get_me(current_user: dict = Depends(get_active_user)):
    return UserProfile(
        username=current_user["username"],
        full_name=current_user["full_name"],
        email=current_user["email"],
        role=current_user["role"],
        department=current_user["department"],
    )


@router.post(
    "/inspect",
    response_model=TokenInspectResponse,
    summary="[Security Audit] Token Inspector - Decode claims without enforcement",
    description=(
        "Security audit utility: decodes and exposes the raw JWT claims. "
        "Does NOT verify the signature - used to inspect tampered or expired tokens. "
        "In production this endpoint would be admin-gated or removed."
    ),
)
def inspect_token(payload: RefreshRequest):
    """Decode token claims without enforcing signature or expiry - audit tool."""
    try:
        # decode_unverified exposes claims regardless of signature or expiry
        claims = jose_jwt.decode(
            payload.refresh_token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": False, "verify_signature": False},
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Token is malformed and cannot be decoded: {str(e)}",
        )

    exp_ts = claims.get("exp")
    iat_ts = claims.get("iat")
    is_expired = False
    if exp_ts:
        is_expired = datetime.fromtimestamp(exp_ts, tz=timezone.utc) < datetime.now(timezone.utc)

    return TokenInspectResponse(
        raw_claims=claims,
        is_expired=is_expired,
        token_type=claims.get("type"),
        subject=claims.get("sub"),
        issued_at=datetime.fromtimestamp(iat_ts, tz=timezone.utc).isoformat() if iat_ts else None,
        expires_at=datetime.fromtimestamp(exp_ts, tz=timezone.utc).isoformat() if exp_ts else None,
    )


# --- Role-Protected Resource Endpoints ---

@router.get(
    "/resources/ledger-report",
    summary="[Auditor+] Retrieve General Ledger Summary Report",
    description="Access restricted to auditor and admin roles. Returns the Q4 LedgerPro financial summary.",
)
def get_ledger_report(current_user: dict = Depends(require_role("auditor", "admin"))):
    return {
        "resource": "Q4-2026 General Ledger Summary Report",
        "accessed_by": current_user["username"],
        "role": current_user["role"],
        "data": {
            "reporting_period": "Q4 2026 (Oct-Dec)",
            "total_billed": 158420.50,
            "total_collected": 119215.25,
            "accounts_receivable": 39205.25,
            "top_client": "Apex Advisory Partners LLC",
            "ledger_balanced": True,
        },
    }


@router.get(
    "/resources/client-list",
    summary="[Accountant+] Retrieve Restricted Client Roster",
    description="Access restricted to accountant, auditor, and admin roles.",
)
def get_client_list(current_user: dict = Depends(require_role("accountant", "auditor", "admin"))):
    return {
        "resource": "LedgerPro Restricted Client Roster",
        "accessed_by": current_user["username"],
        "role": current_user["role"],
        "clients": [
            {"id": "CLI-1001", "name": "Apex Advisory Partners LLC", "status": "Active"},
            {"id": "CLI-1002", "name": "Crestview Logistics UK Ltd", "status": "Active"},
            {"id": "CLI-1003", "name": "Solaria BioTech Inc.", "status": "Under_Audit"},
            {"id": "CLI-1004", "name": "Vanguard Retail Holdings", "status": "Active"},
            {"id": "CLI-1005", "name": "Sterling Financial Trust", "status": "Suspended"},
        ],
    }


@router.get(
    "/resources/public-rates",
    summary="[Any Authenticated User] View LedgerPro Published Service Rates",
    description="Accessible to all authenticated staff regardless of role.",
)
def get_public_rates(current_user: dict = Depends(get_active_user)):
    return {
        "resource": "LedgerPro Published Service Rates (FY2026)",
        "accessed_by": current_user["username"],
        "rates": [
            {"service": "Statutory Financial Audit", "rate_per_hour_usd": 225.0},
            {"service": "Corporate Tax Compliance (Form 1120)", "rate_per_hour_usd": 245.0},
            {"service": "R&D Tax Credit (Section 41)", "rate_per_hour_usd": 275.0},
            {"service": "Fractional CFO Advisory", "rate_per_hour_usd": 195.0},
        ],
    }
