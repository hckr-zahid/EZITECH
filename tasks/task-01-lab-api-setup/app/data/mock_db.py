"""
Mock In-Memory Accounting Database for LedgerPro Accountants.
Populated with realistic corporate accounting datasets (zero lorem-ipsum).
Thread-safe repository supporting CRUD operations and deterministic state resets.
"""

from threading import Lock
from typing import Dict, List, Optional
from datetime import datetime, timezone


class AccountingDataStore:
    def __init__(self):
        self._lock = Lock()
        self.clients: Dict[str, dict] = {}
        self.invoices: Dict[str, dict] = {}
        self.ledger_entries: Dict[str, dict] = {}
        self.seed_database()

    def reset(self):
        """Reset the store back to initial clean seed state (ideal for automated test isolation)."""
        with self._lock:
            self.clients.clear()
            self.invoices.clear()
            self.ledger_entries.clear()
            self.seed_database()

    def seed_database(self):
        """Seed authentic accounting data matching LedgerPro Accountants operations."""
        # 1. Corporate Clients
        seed_clients = [
            {
                "client_id": "CLI-1001",
                "company_name": "Apex Advisory Partners LLC",
                "tax_identifier": "EIN-12-3456789",
                "contact_email": "billing@apexadvisory.com",
                "billing_currency": "USD",
                "credit_limit": 75000.0,
                "status": "Active",
                "outstanding_balance": 18450.0,
                "created_at": "2026-01-15T09:00:00Z",
            },
            {
                "client_id": "CLI-1002",
                "company_name": "Crestview Logistics UK Ltd",
                "tax_identifier": "VAT-GB987654321",
                "contact_email": "finance@crestviewlogistics.co.uk",
                "billing_currency": "GBP",
                "credit_limit": 120000.0,
                "status": "Active",
                "outstanding_balance": 0.0,
                "created_at": "2026-02-10T11:30:00Z",
            },
            {
                "client_id": "CLI-1003",
                "company_name": "Solaria BioTech Inc.",
                "tax_identifier": "EIN-45-8923411",
                "contact_email": "ap@solariabio.com",
                "billing_currency": "USD",
                "credit_limit": 50000.0,
                "status": "Under_Audit",
                "outstanding_balance": 34825.0,
                "created_at": "2026-03-01T14:15:00Z",
            },
            {
                "client_id": "CLI-1004",
                "company_name": "Vanguard Retail Holdings",
                "tax_identifier": "EIN-77-1092384",
                "contact_email": "controller@vanguardretail.com",
                "billing_currency": "USD",
                "credit_limit": 150000.0,
                "status": "Active",
                "outstanding_balance": 9200.0,
                "created_at": "2026-04-18T08:45:00Z",
            },
            {
                "client_id": "CLI-1005",
                "company_name": "Sterling Financial Trust",
                "tax_identifier": "EIN-91-6644210",
                "contact_email": "remittance@sterlingtrust.org",
                "billing_currency": "USD",
                "credit_limit": 25000.0,
                "status": "Suspended",
                "outstanding_balance": 24800.0,
                "created_at": "2026-05-22T16:20:00Z",
            },
        ]
        for c in seed_clients:
            self.clients[c["client_id"]] = c

        # 2. Accounting Service Invoices
        seed_invoices = [
            {
                "invoice_id": "INV-2026-001",
                "invoice_number": "LPA-2026-001",
                "client_id": "CLI-1001",
                "issue_date": "2026-10-15",
                "due_date": "2026-11-15",
                "line_items": [
                    {
                        "description": "Q3 Statutory Financial Audit & Assurance Services",
                        "quantity": 60.0,
                        "unit_price": 225.0,
                    },
                    {
                        "description": "Corporate Tax Compliance & IRS Form 1120 Preparation",
                        "quantity": 20.0,
                        "unit_price": 245.0,
                    },
                ],
                "subtotal": 18400.0,
                "tax_rate": 0.0825,
                "tax_amount": 1518.0,
                "total_amount": 19918.0,
                "status": "Overdue",
                "notes": "Payment terms: Net 30. Wire transfer to LedgerPro Operating Account.",
            },
            {
                "invoice_id": "INV-2026-002",
                "invoice_number": "LPA-2026-002",
                "client_id": "CLI-1003",
                "issue_date": "2026-11-01",
                "due_date": "2026-12-01",
                "line_items": [
                    {
                        "description": "R&D Tax Credit Calculation & Section 41 Substantiation",
                        "quantity": 80.0,
                        "unit_price": 275.0,
                    },
                    {
                        "description": "Multi-Entity Cloud Ledger Reconciliation",
                        "quantity": 35.0,
                        "unit_price": 195.0,
                    },
                ],
                "subtotal": 28825.0,
                "tax_rate": 0.0825,
                "tax_amount": 2378.06,
                "total_amount": 31203.06,
                "status": "Issued",
                "notes": "BioTech Section 41 special compliance documentation attached.",
            },
            {
                "invoice_id": "INV-2026-003",
                "invoice_number": "LPA-2026-003",
                "client_id": "CLI-1004",
                "issue_date": "2026-10-01",
                "due_date": "2026-10-31",
                "line_items": [
                    {
                        "description": "Monthly Executive Fractional CFO Retainer & Financial Review",
                        "quantity": 1.0,
                        "unit_price": 8500.0,
                    }
                ],
                "subtotal": 8500.0,
                "tax_rate": 0.0825,
                "tax_amount": 701.25,
                "total_amount": 9201.25,
                "status": "Paid",
                "notes": "Paid in full via ACH Direct Debit on 2026-10-28.",
            },
        ]
        for inv in seed_invoices:
            self.invoices[inv["invoice_id"]] = inv

        # 3. Double-Entry General Ledger Transactions
        seed_ledger = [
            {
                "entry_id": "GL-2026-101",
                "entry_number": "JRNL-00101",
                "transaction_date": "2026-10-15",
                "reference": "INV-2026-001",
                "description": "Recognition of Accounts Receivable and Audit Revenue for Apex Advisory",
                "lines": [
                    {
                        "account_code": "1200",
                        "account_name": "Accounts Receivable",
                        "debit": 19918.0,
                        "credit": 0.0,
                    },
                    {
                        "account_code": "4010",
                        "account_name": "Audit & Assurance Revenue",
                        "debit": 0.0,
                        "credit": 18400.0,
                    },
                    {
                        "account_code": "2200",
                        "account_name": "Sales & Services Tax Payable",
                        "debit": 0.0,
                        "credit": 1518.0,
                    },
                ],
                "total_amount": 19918.0,
                "created_at": "2026-10-15T10:00:00Z",
            },
            {
                "entry_id": "GL-2026-102",
                "entry_number": "JRNL-00102",
                "transaction_date": "2026-10-28",
                "reference": "INV-2026-003",
                "description": "Cash receipt settlement for Vanguard Retail Holdings retainer",
                "lines": [
                    {
                        "account_code": "1010",
                        "account_name": "Operating Cash Account",
                        "debit": 9201.25,
                        "credit": 0.0,
                    },
                    {
                        "account_code": "1200",
                        "account_name": "Accounts Receivable",
                        "debit": 0.0,
                        "credit": 9201.25,
                    },
                ],
                "total_amount": 9201.25,
                "created_at": "2026-10-28T14:30:00Z",
            },
        ]
        for gl in seed_ledger:
            self.ledger_entries[gl["entry_id"]] = gl

    # CRUD & Helper methods
    def get_all_clients(self) -> List[dict]:
        with self._lock:
            return list(self.clients.values())

    def get_client(self, client_id: str) -> Optional[dict]:
        with self._lock:
            return self.clients.get(client_id)

    def add_client(self, client_data: dict) -> dict:
        with self._lock:
            cid = f"CLI-{1000 + len(self.clients) + 1}"
            client_record = {
                "client_id": cid,
                **client_data,
                "status": "Active",
                "outstanding_balance": 0.0,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            self.clients[cid] = client_record
            return client_record

    def get_all_invoices(self, status: Optional[str] = None) -> List[dict]:
        with self._lock:
            invoices = list(self.invoices.values())
            if status:
                invoices = [i for i in invoices if i["status"].lower() == status.lower()]
            return invoices

    def get_invoice(self, invoice_id: str) -> Optional[dict]:
        with self._lock:
            return self.invoices.get(invoice_id)

    def add_invoice(self, invoice_data: dict) -> dict:
        with self._lock:
            inv_count = len(self.invoices) + 1
            inv_id = f"INV-2026-{inv_count:03d}"
            inv_num = f"LPA-2026-{inv_count:03d}"

            # Calculate totals
            subtotal = round(
                sum(item["quantity"] * item["unit_price"] for item in invoice_data["line_items"]),
                2,
            )
            tax_rate = invoice_data.get("tax_rate", 0.0825)
            tax_amount = round(subtotal * tax_rate, 2)
            total_amount = round(subtotal + tax_amount, 2)

            invoice_record = {
                "invoice_id": inv_id,
                "invoice_number": inv_num,
                "client_id": invoice_data["client_id"],
                "issue_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "due_date": invoice_data["due_date"],
                "line_items": invoice_data["line_items"],
                "subtotal": subtotal,
                "tax_rate": tax_rate,
                "tax_amount": tax_amount,
                "total_amount": total_amount,
                "status": "Issued",
                "notes": invoice_data.get("notes"),
            }
            self.invoices[inv_id] = invoice_record

            # Update client balance if client exists
            if invoice_data["client_id"] in self.clients:
                self.clients[invoice_data["client_id"]]["outstanding_balance"] += total_amount

            return invoice_record

    def get_all_ledger_entries(self) -> List[dict]:
        with self._lock:
            return list(self.ledger_entries.values())

    def get_ledger_entry(self, entry_id: str) -> Optional[dict]:
        with self._lock:
            return self.ledger_entries.get(entry_id)

    def add_ledger_entry(self, entry_data: dict) -> dict:
        with self._lock:
            gl_count = len(self.ledger_entries) + 1
            entry_id = f"GL-2026-{100 + gl_count}"
            entry_num = f"JRNL-{100 + gl_count:05d}"
            total_amount = round(sum(line["debit"] for line in entry_data["lines"]), 2)

            record = {
                "entry_id": entry_id,
                "entry_number": entry_num,
                "transaction_date": entry_data["transaction_date"],
                "reference": entry_data["reference"],
                "description": entry_data["description"],
                "lines": entry_data["lines"],
                "total_amount": total_amount,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            self.ledger_entries[entry_id] = record
            return record

    def get_summary_metrics(self) -> dict:
        with self._lock:
            all_entries = list(self.ledger_entries.values())
            total_debits = sum(sum(l["debit"] for l in e["lines"]) for e in all_entries)
            total_credits = sum(sum(l["credit"] for l in e["lines"]) for e in all_entries)

            ar_balance = sum(
                l["debit"] - l["credit"]
                for e in all_entries
                for l in e["lines"]
                if l["account_code"] == "1200"
            )
            cash_balance = sum(
                l["debit"] - l["credit"]
                for e in all_entries
                for l in e["lines"]
                if l["account_code"] == "1010"
            )
            revenue_posted = sum(
                l["credit"] - l["debit"]
                for e in all_entries
                for l in e["lines"]
                if l["account_code"].startswith("4")
            )

            return {
                "total_journal_entries": len(all_entries),
                "total_debits_posted": round(total_debits, 2),
                "total_credits_posted": round(total_credits, 2),
                "is_ledger_balanced": round(total_debits, 2) == round(total_credits, 2),
                "accounts_receivable_balance": round(ar_balance, 2),
                "operating_cash_balance": round(cash_balance, 2),
                "total_revenue_recognized": round(revenue_posted, 2),
            }


db = AccountingDataStore()
