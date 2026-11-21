"""
LedgerPro Accountants - Task 2: FastAPI Dependencies
Bearer token extraction, current user resolution, and RBAC enforcement.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from app.auth.jwt_handler import decode_token
from app.data.users import get_user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Role hierarchy: each role includes all permissions of roles below it.
ROLE_HIERARCHY = {
    "admin":      {"admin", "auditor", "accountant", "viewer"},
    "auditor":    {"auditor", "accountant", "viewer"},
    "accountant": {"accountant", "viewer"},
    "viewer":     {"viewer"},
}


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Validate the Bearer JWT and return the authenticated user dict.
    Raises 401 for: missing token, expired token, tampered signature,
    missing 'sub' claim, wrong token type (e.g. refresh used as access).
    """
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials. Token is missing, expired, or tampered.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        username: str = payload.get("sub")
        token_type: str = payload.get("type")

        if username is None:
            raise credentials_exc
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type. Supply an access token, not a refresh token.",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise credentials_exc

    user = get_user(username)
    if user is None:
        raise credentials_exc
    return user


def get_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Block deactivated / offboarded staff accounts."""
    if current_user.get("disabled"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account '{current_user['username']}' has been deactivated. Contact LedgerPro IT.",
        )
    return current_user


def require_role(*required_roles: str):
    """
    Factory dependency - returns a FastAPI dependency that enforces
    that the caller's role appears in `required_roles` (or higher via hierarchy).
    Usage: Depends(require_role("admin", "auditor"))
    """
    def role_checker(current_user: dict = Depends(get_active_user)) -> dict:
        user_role = current_user.get("role", "")
        allowed = ROLE_HIERARCHY.get(user_role, set())
        if not any(r in allowed for r in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access denied. Your role '{user_role}' does not have permission "
                    f"for this resource. Required: {list(required_roles)}."
                ),
            )
        return current_user
    return role_checker
