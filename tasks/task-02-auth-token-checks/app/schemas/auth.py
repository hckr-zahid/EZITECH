"""
LedgerPro Accountants - Task 2: Auth & Token Schemas
"""

from typing import Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(
        ..., min_length=3, max_length=80,
        description="LedgerPro staff username (firstname.lastname format)",
        examples=["fatima.zahra"],
    )
    password: str = Field(
        ..., min_length=6, max_length=128,
        description="Staff account password",
    )


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    role: str
    username: str


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., description="Valid refresh token issued at login")


class UserProfile(BaseModel):
    username: str
    full_name: str
    email: str
    role: str
    department: str


class TokenInspectResponse(BaseModel):
    """Security audit endpoint: decodes a token and returns its claims without verifying signature."""
    raw_claims: dict
    is_expired: bool
    token_type: Optional[str]
    subject: Optional[str]
    issued_at: Optional[str]
    expires_at: Optional[str]
