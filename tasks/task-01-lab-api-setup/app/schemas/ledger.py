"""
General Ledger (GL) domain schemas for LedgerPro Accountants.
Supports standard double-entry bookkeeping validation.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator


class AccountType(str, Enum):
    ASSET = "Asset"
    LIABILITY = "Liability"
    EQUITY = "Equity"
    REVENUE = "Revenue"
    EXPENSE = "Expense"


class LedgerLine(BaseModel):
    account_code: str = Field(
        ...,
        pattern=r"^\d{4}$",
        description="4-digit standard chart of accounts code (e.g. 1010, 1200, 4010)",
        examples=["1010", "4010"],
    )
    account_name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Accounting ledger account name",
        examples=["Operating Cash Account", "Tax Advisory Revenue"],
    )
    debit: float = Field(
        default=0.0,
        ge=0.0,
        description="Debit amount in ledger currency",
    )
    credit: float = Field(
        default=0.0,
        ge=0.0,
        description="Credit amount in ledger currency",
    )

    @model_validator(mode="after")
    def validate_single_sided_line(self):
        if self.debit > 0 and self.credit > 0:
            raise ValueError("A single ledger line cannot contain both debit and credit amounts.")
        if self.debit == 0 and self.credit == 0:
            raise ValueError("A ledger line must contain a non-zero debit or credit amount.")
        return self


class LedgerEntryCreate(BaseModel):
    transaction_date: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Date of accounting entry (YYYY-MM-DD)",
        examples=["2026-11-20"],
    )
    reference: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Source document reference (e.g. INV-2026-089, TX-PAY-004)",
        examples=["INV-2026-089"],
    )
    description: str = Field(
        ...,
        min_length=5,
        max_length=250,
        description="Journal entry explanation",
        examples=["Revenue recognition for Apex Advisory Q3 Audit"],
    )
    lines: List[LedgerLine] = Field(
        ...,
        min_length=2,
        description="At least two balanced ledger lines are required for double-entry bookkeeping",
    )

    @model_validator(mode="after")
    def validate_balanced_entry(self):
        total_debit = round(sum(line.debit for line in self.lines), 2)
        total_credit = round(sum(line.credit for line in self.lines), 2)
        if total_debit != total_credit:
            raise ValueError(
                f"Unbalanced journal entry: Total debits (${total_debit:.2f}) must equal total credits (${total_credit:.2f})."
            )
        return self


class LedgerEntryResponse(BaseModel):
    entry_id: str
    entry_number: str
    transaction_date: str
    reference: str
    description: str
    lines: List[LedgerLine]
    total_amount: float
    created_at: str


class LedgerSummaryResponse(BaseModel):
    total_journal_entries: int
    total_debits_posted: float
    total_credits_posted: float
    is_ledger_balanced: bool
    accounts_receivable_balance: float
    operating_cash_balance: float
    total_revenue_recognized: float
