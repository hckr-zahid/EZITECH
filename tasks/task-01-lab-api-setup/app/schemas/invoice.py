"""
Invoice domain schemas for LedgerPro Accountants.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator


class InvoiceStatus(str, Enum):
    DRAFT = "Draft"
    ISSUED = "Issued"
    PAID = "Paid"
    OVERDUE = "Overdue"
    CANCELLED = "Cancelled"


class InvoiceLineItem(BaseModel):
    description: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Detailed description of professional accounting service",
        examples=["Q3 Statutory Financial Audit & Assurance"],
    )
    quantity: float = Field(
        ...,
        gt=0.0,
        description="Billed hours or service unit quantity",
        examples=[40.0],
    )
    unit_price: float = Field(
        ...,
        gt=0.0,
        description="Hourly billing rate or unit service fee in USD",
        examples=[185.0],
    )

    @property
    def line_total(self) -> float:
        return round(self.quantity * self.unit_price, 2)


class InvoiceCreate(BaseModel):
    client_id: str = Field(..., description="Target client identifier")
    line_items: List[InvoiceLineItem] = Field(
        ...,
        min_length=1,
        description="At least one accounting service line item required",
    )
    tax_rate: float = Field(
        default=0.0825,
        ge=0.0,
        le=0.50,
        description="Applicable jurisdiction sales / corporate services tax rate (e.g. 0.0825 for 8.25%)",
    )
    due_date: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Payment due date formatted as YYYY-MM-DD",
        examples=["2026-12-15"],
    )
    notes: Optional[str] = Field(
        None,
        max_length=500,
        description="Compliance or remittance notes",
    )


class InvoiceResponse(BaseModel):
    invoice_id: str
    invoice_number: str
    client_id: str
    issue_date: str
    due_date: str
    line_items: List[InvoiceLineItem]
    subtotal: float
    tax_rate: float
    tax_amount: float
    total_amount: float
    status: InvoiceStatus
    notes: Optional[str] = None
