"""
General Ledger routes for LedgerPro Accountants.
"""

from typing import List
from fastapi import APIRouter, HTTPException, status
from app.schemas.ledger import LedgerEntryCreate, LedgerEntryResponse, LedgerSummaryResponse
from app.data.mock_db import db

router = APIRouter(prefix="/ledger", tags=["General Ledger & Financial Reporting"])


@router.get(
    "/entries",
    response_model=List[LedgerEntryResponse],
    summary="List all General Ledger journal entries",
    description="Retrieve posted double-entry journal records showing accounts, debits, and credits.",
)
def list_ledger_entries():
    return db.get_all_ledger_entries()


@router.get(
    "/entries/{entry_id}",
    response_model=LedgerEntryResponse,
    summary="Get journal entry by ID",
    description="Retrieve a single journal entry transaction voucher.",
)
def get_ledger_entry(entry_id: str):
    entry = db.get_ledger_entry(entry_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"General Ledger entry '{entry_id}' not found.",
        )
    return entry


@router.post(
    "/entries",
    response_model=LedgerEntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Post a new balanced double-entry journal transaction",
    description="Record financial transaction. Enforces fundamental accounting equation: Total Debits == Total Credits.",
)
def create_ledger_entry(payload: LedgerEntryCreate):
    entry = db.add_ledger_entry(payload.model_dump())
    return entry


@router.get(
    "/summary",
    response_model=LedgerSummaryResponse,
    summary="Get financial ledger summary & balance status",
    description="Provides real-time audit verification that the general ledger is in balance.",
)
def get_ledger_summary():
    return db.get_summary_metrics()
