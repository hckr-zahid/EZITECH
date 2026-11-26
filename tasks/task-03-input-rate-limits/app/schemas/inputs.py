"""
Pydantic v2 request/response models for Task 3 input validation endpoints.
All fields validated at the schema layer so the route never sees raw user input.
"""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Shared validators
# ---------------------------------------------------------------------------

_SAFE_TEXT_RE = re.compile(r"^[A-Za-z0-9 .,&'()\-]+$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Hard-blocked tokens that always indicate injection attempts
_SQL_HARD_TOKENS = [";", "--", "/*", "*/", "xp_", "drop ", "insert ", "select ", "union "]
_HTML_TOKENS = ["<script", "<img", "javascript:", "onerror=", "onload="]

# Context pattern: digit-or-quote SPACE or/and SPACE digit-or-quote
# e.g. "' or 1=1" or "1 or 1" - but NOT "VAT and payroll"
_SQL_LOGIC_RE = re.compile(r"""[\d'"][\s]+(or|and)[\s]+[\d'"]""")
# Quote characters immediately followed by logic word
_QUOTE_LOGIC_RE = re.compile(r"""'[\s]*(or|and)[\s]*'""")


def _reject_injection(value: str, field_name: str) -> str:
    """
    Reject strings that contain SQL or HTML injection patterns.
    Plain English conjunctions like 'and' and 'or' are allowed in
    natural accounting text. They are only flagged when adjacent to
    digits or quotation marks (classic numeric SQLi: 1 OR 1=1).
    """
    lower = value.lower()

    # Always-blocked SQL tokens
    for token in _SQL_HARD_TOKENS:
        if token in lower:
            raise ValueError(f"{field_name} contains a disallowed pattern: {token!r}")

    # Quote + logic word pattern (SQL injection idiom)
    if _QUOTE_LOGIC_RE.search(lower):
        raise ValueError(f"{field_name} contains a SQL injection pattern.")

    # Digit-flanked or/and logic (numeric SQLi)
    if _SQL_LOGIC_RE.search(lower):
        raise ValueError(f"{field_name} contains a SQL logic pattern.")

    # HTML / XSS tokens
    for token in _HTML_TOKENS:
        if token in lower:
            raise ValueError(f"{field_name} contains a disallowed pattern: {token!r}")

    return value


# ---------------------------------------------------------------------------
# Client intake form
# ---------------------------------------------------------------------------

class ClientIntakeRequest(BaseModel):
    """Submitted when onboarding a new accounting client."""

    client_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Legal name of the client company.",
        examples=["Crescent Textile Mills Ltd"],
    )
    contact_email: str = Field(
        ...,
        max_length=254,
        description="Primary contact email address.",
        examples=["accounts@crescenttextile.pk"],
    )
    annual_revenue: Decimal = Field(
        ...,
        ge=Decimal("0"),
        le=Decimal("10000000"),
        description="Declared annual revenue in GBP, used for fee banding.",
        examples=[Decimal("2500000.00")],
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional notes about the client engagement.",
    )

    @field_validator("client_name")
    @classmethod
    def validate_client_name(cls, v: str) -> str:
        v = v.strip()
        # Reject quotes in name (apostrophes in Irish/Scottish names are edge cases
        # not in scope for this lab; the validator keeps things simple)
        if re.search(r"['\"]", v):
            raise ValueError("client_name must not contain quote characters.")
        return _reject_injection(v, "client_name")

    @field_validator("contact_email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not _EMAIL_RE.match(v):
            raise ValueError("contact_email is not a valid email address.")
        return _reject_injection(v, "contact_email")

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        return _reject_injection(v, "description")


class ClientIntakeResponse(BaseModel):
    client_id: str
    client_name: str
    contact_email: str
    annual_revenue: Decimal
    message: str


# ---------------------------------------------------------------------------
# Invoice submission
# ---------------------------------------------------------------------------

class InvoiceSubmitRequest(BaseModel):
    """Posted when raising an invoice against an existing client."""

    client_id: str = Field(
        ...,
        min_length=4,
        max_length=20,
        pattern=r"^CLI-[0-9]{4}$",
        description="Client identifier, format CLI-NNNN.",
        examples=["CLI-0042"],
    )
    invoice_ref: str = Field(
        ...,
        min_length=4,
        max_length=30,
        pattern=r"^INV-[0-9]{4,6}$",
        description="Invoice reference number, format INV-NNNNNN.",
        examples=["INV-100122"],
    )
    amount: Decimal = Field(
        ...,
        gt=Decimal("0"),
        le=Decimal("10000000"),
        description="Invoice amount in GBP, must be positive.",
        examples=[Decimal("4800.00")],
    )
    line_item: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Description of work or service billed.",
        examples=["Quarterly VAT return preparation - Q3 2026"],
    )

    @field_validator("line_item")
    @classmethod
    def validate_line_item(cls, v: str) -> str:
        v = v.strip()
        return _reject_injection(v, "line_item")


class InvoiceSubmitResponse(BaseModel):
    invoice_ref: str
    client_id: str
    amount: Decimal
    status: str
    message: str


# ---------------------------------------------------------------------------
# Ledger entry
# ---------------------------------------------------------------------------

class LedgerEntryRequest(BaseModel):
    """Posts a double-entry ledger line."""

    account_code: str = Field(
        ...,
        pattern=r"^[0-9]{4,6}$",
        description="Nominal account code, 4 to 6 digits.",
        examples=["4000"],
    )
    debit: Decimal = Field(
        default=Decimal("0"),
        ge=Decimal("0"),
        le=Decimal("10000000"),
    )
    credit: Decimal = Field(
        default=Decimal("0"),
        ge=Decimal("0"),
        le=Decimal("10000000"),
    )
    narrative: str = Field(
        ...,
        min_length=5,
        max_length=300,
        description="Plain-language description of the transaction.",
        examples=["Payment received - Crescent Textile Mills Q3 invoice"],
    )

    @model_validator(mode="after")
    def check_debit_xor_credit(self) -> "LedgerEntryRequest":
        if self.debit > 0 and self.credit > 0:
            raise ValueError("A ledger entry must have either a debit or a credit, not both.")
        if self.debit == 0 and self.credit == 0:
            raise ValueError("A ledger entry must have a non-zero debit or credit.")
        return self

    @field_validator("narrative")
    @classmethod
    def validate_narrative(cls, v: str) -> str:
        v = v.strip()
        return _reject_injection(v, "narrative")


class LedgerEntryResponse(BaseModel):
    entry_id: str
    account_code: str
    debit: Decimal
    credit: Decimal
    narrative: str
    message: str
