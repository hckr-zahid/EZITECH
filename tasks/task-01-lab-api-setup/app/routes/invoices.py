"""
Invoice management routes for LedgerPro Accountants.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from app.schemas.invoice import InvoiceCreate, InvoiceResponse, InvoiceStatus
from app.data.mock_db import db

router = APIRouter(prefix="/invoices", tags=["Invoicing & Billing"])


@router.get(
    "",
    response_model=List[InvoiceResponse],
    summary="List all invoices",
    description="Retrieve invoices with optional status filtering (Draft, Issued, Paid, Overdue).",
)
def list_invoices(
    status_filter: Optional[InvoiceStatus] = Query(
        None,
        alias="status",
        description="Filter by invoice status",
    )
):
    status_val = status_filter.value if status_filter else None
    return db.get_all_invoices(status=status_val)


@router.get(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    summary="Get invoice details",
    description="Retrieve line items, calculated subtotal, taxes, and status for a specific invoice.",
)
def get_invoice(invoice_id: str):
    invoice = db.get_invoice(invoice_id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID '{invoice_id}' was not found.",
        )
    return invoice


@router.post(
    "",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new accounting invoice",
    description="Issue an invoice to a registered client with itemized professional accounting services.",
)
def create_invoice(payload: InvoiceCreate):
    # Verify client exists
    client = db.get_client(payload.client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot issue invoice: Target client '{payload.client_id}' does not exist.",
        )

    # Verify client is not suspended
    if client.get("status") == "Suspended":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot issue invoice: Client '{client['company_name']}' account is suspended.",
        )

    # Serialize payload
    data = payload.model_dump()
    new_inv = db.add_invoice(data)
    return new_inv


@router.post(
    "/{invoice_id}/pay",
    response_model=InvoiceResponse,
    summary="Record payment for an invoice",
    description="Mark an issued or overdue invoice as paid and settle client outstanding balance.",
)
def record_payment(invoice_id: str):
    invoice = db.get_invoice(invoice_id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice '{invoice_id}' not found.",
        )
    if invoice["status"] == "Paid":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invoice '{invoice_id}' is already marked as Paid.",
        )

    invoice["status"] = "Paid"
    client = db.get_client(invoice["client_id"])
    if client:
        client["outstanding_balance"] = max(0.0, client["outstanding_balance"] - invoice["total_amount"])

    return invoice
