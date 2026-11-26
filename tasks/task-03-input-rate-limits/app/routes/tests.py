"""
Task 3 - LedgerPro Accountants: Input and Rate Limit Tests
Route handlers for client intake, invoice submission, and ledger entry.
Each endpoint demonstrates Pydantic v2 validation and returns structured errors.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Request

from app.schemas.inputs import (
    ClientIntakeRequest, ClientIntakeResponse,
    InvoiceSubmitRequest, InvoiceSubmitResponse,
    LedgerEntryRequest, LedgerEntryResponse,
)

router = APIRouter(prefix="/api/v1", tags=["input-tests"])


# ---------------------------------------------------------------------------
# Client intake
# ---------------------------------------------------------------------------

@router.post(
    "/clients",
    response_model=ClientIntakeResponse,
    summary="Onboard a new accounting client",
)
async def create_client(payload: ClientIntakeRequest) -> ClientIntakeResponse:
    """
    Accepts a client intake form.
    Pydantic rejects oversized strings, injection patterns, and malformed emails
    before this handler is called; a 422 is returned automatically.
    """
    client_id = f"CLI-{uuid.uuid4().hex[:4].upper()}"
    return ClientIntakeResponse(
        client_id=client_id,
        client_name=payload.client_name,
        contact_email=payload.contact_email,
        annual_revenue=payload.annual_revenue,
        message="Client record created successfully.",
    )


# ---------------------------------------------------------------------------
# Invoice submission
# ---------------------------------------------------------------------------

@router.post(
    "/invoices",
    response_model=InvoiceSubmitResponse,
    summary="Raise an invoice against a client",
)
async def submit_invoice(payload: InvoiceSubmitRequest) -> InvoiceSubmitResponse:
    """
    Validates invoice format, amount ceiling, and line item text.
    Negative amounts, zero amounts, and amounts above 10,000,000 are rejected.
    """
    return InvoiceSubmitResponse(
        invoice_ref=payload.invoice_ref,
        client_id=payload.client_id,
        amount=payload.amount,
        status="pending",
        message="Invoice queued for review.",
    )


# ---------------------------------------------------------------------------
# Ledger entry
# ---------------------------------------------------------------------------

@router.post(
    "/ledger",
    response_model=LedgerEntryResponse,
    summary="Post a double-entry ledger line",
)
async def post_ledger_entry(payload: LedgerEntryRequest) -> LedgerEntryResponse:
    """
    Validates that exactly one of debit/credit is non-zero (double-entry rule).
    Returns 422 if both are set or both are zero.
    """
    entry_id = f"TXN-{uuid.uuid4().hex[:6].upper()}"
    return LedgerEntryResponse(
        entry_id=entry_id,
        account_code=payload.account_code,
        debit=payload.debit,
        credit=payload.credit,
        narrative=payload.narrative,
        message="Ledger entry recorded.",
    )


# ---------------------------------------------------------------------------
# Rate limit probe endpoint (read-only, cheap to call)
# ---------------------------------------------------------------------------

@router.get(
    "/ping",
    summary="Health check - subject to rate limiting in production",
)
async def ping(request: Request) -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "task-03-input-rate-limits",
        "client_host": request.client.host if request.client else "unknown",
    }
