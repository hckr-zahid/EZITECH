"""
Client domain schemas for LedgerPro Accountants.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class ClientStatus(str, Enum):
    ACTIVE = "Active"
    SUSPENDED = "Suspended"
    UNDER_AUDIT = "Under_Audit"
    INACTIVE = "Inactive"


class ClientBase(BaseModel):
    company_name: str = Field(
        ...,
        min_length=2,
        max_length=150,
        description="Legal registered corporate entity name",
        examples=["Apex Advisory Partners LLC"],
    )
    tax_identifier: str = Field(
        ...,
        min_length=5,
        max_length=30,
        description="Federal EIN or VAT Registration Number",
        examples=["EIN-12-3456789"],
    )
    contact_email: EmailStr = Field(
        ...,
        description="Primary billing and compliance contact email",
        examples=["finance@apexadvisory.com"],
    )
    billing_currency: str = Field(
        default="USD",
        min_length=3,
        max_length=3,
        description="ISO 4217 Currency Code",
        examples=["USD", "GBP", "EUR"],
    )
    credit_limit: float = Field(
        default=50000.0,
        ge=0.0,
        description="Authorized credit limit in billing currency",
    )


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    company_name: Optional[str] = Field(None, min_length=2, max_length=150)
    contact_email: Optional[EmailStr] = None
    status: Optional[ClientStatus] = None
    credit_limit: Optional[float] = Field(None, ge=0.0)


class ClientResponse(ClientBase):
    client_id: str = Field(..., description="Unique client system identifier")
    status: ClientStatus = Field(default=ClientStatus.ACTIVE)
    outstanding_balance: float = Field(
        default=0.0,
        description="Current unpaid balance across all issued invoices",
    )
    created_at: str
