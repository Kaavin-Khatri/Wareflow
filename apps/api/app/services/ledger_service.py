"""Domain service for Accounts-Receivable (AR) statement and retailer ledger calculation."""

from datetime import datetime
from typing import Any

from fastapi import HTTPException, status

from app.repositories.interfaces.invoice_repository import InvoiceRepositoryInterface
from app.repositories.interfaces.payment_repository import PaymentRepositoryInterface
from app.repositories.interfaces.retailer_repository import RetailerRepository
from app.schemas.billing import LedgerEntryResponse, RetailerLedgerResponse


class LedgerService:
    """Calculates live chronological statement and paired Accounts-Receivable ledger per retailer."""

    def __init__(
        self,
        retailer_repo: RetailerRepository,
        invoice_repo: InvoiceRepositoryInterface,
        payment_repo: PaymentRepositoryInterface,
    ) -> None:
        self.retailer_repo = retailer_repo
        self.invoice_repo = invoice_repo
        self.payment_repo = payment_repo

    def get_retailer_ledger(self, retailer_id: str) -> RetailerLedgerResponse:
        """
        Generate a complete chronological statement for a wholesale retailer.

        Every invoice charges AR (+debit) and every payment settles AR (-credit).
        The running balance tracks cumulative balance owed and matches retailer.credit_balance.
        """
        retailer = self.retailer_repo.get_by_id(retailer_id)
        if not retailer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Retailer '{retailer_id}' not found.",
            )

        invoices = self.invoice_repo.list_by_retailer_id(retailer_id)
        payments = self.payment_repo.list_by_retailer_id(retailer_id)

        raw_events: list[dict[str, Any]] = []

        # 1. Map Invoices as Debit charges (+)
        for inv in invoices:
            so_ref = inv.sales_order.so_number if getattr(inv, "sales_order", None) else "Direct"
            inv_date = inv.invoice_date or inv.created_at
            raw_events.append(
                {
                    "id": inv.id,
                    "date": inv_date,
                    "entry_type": "invoice",
                    "reference_no": inv.invoice_no,
                    "description": f"Tax Invoice ({so_ref})",
                    "debit_amount": float(inv.total_amount),
                    "credit_amount": 0.0,
                    "status": str(inv.status),
                }
            )

        # 2. Map Payments as Credit settlements (-)
        for p in payments:
            pay_date = p.paid_at or p.created_at
            method_label = (
                p.method.value.replace("_", " ").upper()
                if hasattr(p.method, "value")
                else str(p.method).upper()
            )
            desc = f"Payment received via {method_label}"
            if p.note:
                desc += f" — {p.note}"

            raw_events.append(
                {
                    "id": p.id,
                    "date": pay_date,
                    "entry_type": "payment",
                    "reference_no": f"PAY-{p.id[:8].upper()}",
                    "description": desc,
                    "debit_amount": 0.0,
                    "credit_amount": float(p.amount),
                    "status": "settled",
                }
            )

        # 3. Sort chronologically (Invoices before Payments if identical timestamp)
        sorted_events = sorted(
            raw_events,
            key=lambda x: (
                x["date"] if isinstance(x["date"], datetime) else datetime.min,
                0 if x["entry_type"] == "invoice" else 1,
            ),
        )

        # 4. Compute running balance
        running_bal = 0.0
        total_invoiced = 0.0
        total_paid = 0.0
        ledger_entries: list[LedgerEntryResponse] = []

        for ev in sorted_events:
            if ev["entry_type"] == "invoice":
                running_bal = round(running_bal + ev["debit_amount"], 2)
                total_invoiced = round(total_invoiced + ev["debit_amount"], 2)
            else:
                running_bal = round(running_bal - ev["credit_amount"], 2)
                total_paid = round(total_paid + ev["credit_amount"], 2)

            ledger_entries.append(
                LedgerEntryResponse(
                    id=ev["id"],
                    date=ev["date"],
                    entry_type=ev["entry_type"],
                    reference_no=ev["reference_no"],
                    description=ev["description"],
                    debit_amount=ev["debit_amount"],
                    credit_amount=ev["credit_amount"],
                    running_balance=running_bal,
                    status=ev["status"],
                )
            )

        current_balance = float(retailer.credit_balance or 0.0)
        credit_limit = float(retailer.credit_limit or 0.0)
        available_credit = max(0.0, round(credit_limit - current_balance, 2))

        return RetailerLedgerResponse(
            retailer_id=retailer.id,
            retailer_name=retailer.name,
            gstin=getattr(retailer, "gstin", None),
            credit_limit=credit_limit,
            current_credit_balance=current_balance,
            available_credit=available_credit,
            total_invoiced=total_invoiced,
            total_paid=total_paid,
            entries=ledger_entries,
        )
