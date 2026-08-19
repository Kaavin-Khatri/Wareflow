"""Domain service for Payment recording, invoice status transitions, and overdue detection."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from fastapi import HTTPException, status

if TYPE_CHECKING:
    from app.core.security import CurrentUser

from app.models.billing import Invoice, InvoiceStatusEnum, Payment
from app.repositories.interfaces.audit_repository import AuditRepository
from app.repositories.interfaces.invoice_repository import InvoiceRepositoryInterface
from app.repositories.interfaces.payment_repository import PaymentRepositoryInterface
from app.repositories.interfaces.retailer_repository import RetailerRepository
from app.schemas.billing import (
    OverdueDetectionResponse,
    PaymentCreateRequest,
    PaymentResponse,
)


class PaymentService:
    """Business domain logic for recording payments against invoices and updating credit."""

    def __init__(
        self,
        payment_repo: PaymentRepositoryInterface,
        invoice_repo: InvoiceRepositoryInterface,
        retailer_repo: RetailerRepository,
        audit_repo: AuditRepository | None = None,
    ) -> None:
        self.payment_repo = payment_repo
        self.invoice_repo = invoice_repo
        self.retailer_repo = retailer_repo
        self.audit_repo = audit_repo

    def record_payment(
        self,
        invoice_id: str,
        payload: PaymentCreateRequest,
        current_user: CurrentUser | None = None,
    ) -> PaymentResponse:
        """
        Record a payment against a tax invoice.

        Validates outstanding balance, updates invoice status (unpaid -> partially_paid -> paid),
        and decreases retailer credit_balance by the exact payment amount.
        """
        invoice = self.invoice_repo.get_by_id(invoice_id)
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice '{invoice_id}' not found.",
            )

        if invoice.status == InvoiceStatusEnum.PAID:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invoice '{invoice.invoice_no}' has already been fully settled.",
            )

        # Calculate current outstanding balance
        prior_paid = self.payment_repo.get_total_paid_for_invoice(invoice_id)
        total_inv_amount = float(invoice.total_amount)
        outstanding = round(total_inv_amount - prior_paid, 2)

        if payload.amount > outstanding + 0.001:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Payment amount (₹{payload.amount:,.2f}) exceeds the outstanding balance "
                    f"(₹{outstanding:,.2f}) for invoice {invoice.invoice_no}."
                ),
            )

        # Resolve buyer reference
        retailer_id = None
        customer_id = None
        if invoice.sales_order:
            retailer_id = invoice.sales_order.retailer_id
            customer_id = invoice.sales_order.customer_id

        # Persist payment
        now = datetime.now(UTC)
        paid_at_time = payload.paid_at or now
        payment = Payment(
            id=str(uuid.uuid4()),
            invoice_id=invoice.id,
            retailer_id=retailer_id,
            customer_id=customer_id,
            amount=payload.amount,
            method=payload.method,
            paid_at=paid_at_time,
            note=payload.note,
            created_at=now,
        )
        created_payment = self.payment_repo.create(payment)


        # Update invoice payment status
        new_cumulative_paid = round(prior_paid + payload.amount, 2)
        if new_cumulative_paid >= total_inv_amount - 0.001:
            invoice.status = InvoiceStatusEnum.PAID
        elif new_cumulative_paid > 0:
            invoice.status = InvoiceStatusEnum.PARTIALLY_PAID

        self.invoice_repo.update_invoice(invoice)

        # DECREASE retailer credit_balance (credit_balance represents amount currently owed)
        if retailer_id:
            retailer = self.retailer_repo.get_by_id(retailer_id)
            if retailer:
                current_bal = float(retailer.credit_balance or 0.0)
                new_bal = max(0.0, round(current_bal - payload.amount, 2))
                self.retailer_repo.update(retailer_id, {"credit_balance": new_bal})

        # Audit log
        if self.audit_repo:
            self.audit_repo.create_log(
                actor_id=current_user.id if current_user else "system",
                action="payment_recorded",
                entity_type="payment",
                entity_id=created_payment.id,
                before_value={"invoice_status": str(invoice.status), "prior_paid": prior_paid},
                after_value={
                    "payment_amount": payload.amount,
                    "payment_method": str(payload.method),
                    "invoice_status": str(invoice.status),
                    "new_cumulative_paid": new_cumulative_paid,
                },
            )

        return self._to_payment_response(created_payment, invoice)

    def list_payments_for_invoice(self, invoice_id: str) -> list[PaymentResponse]:
        """Fetch all payment records for an invoice."""
        invoice = self.invoice_repo.get_by_id(invoice_id)
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice '{invoice_id}' not found.",
            )
        payments = self.payment_repo.list_by_invoice_id(invoice_id)
        return [self._to_payment_response(p, invoice) for p in payments]

    def detect_overdue_invoices(
        self,
        due_days: int = 30,
        current_user: CurrentUser | None = None,
    ) -> OverdueDetectionResponse:
        """
        Scan all unpaid and partially-paid invoices older than the due-window and mark them overdue.

        Feeds Phase 11 alerts and accounts receivable tracking.
        """
        cutoff_date = datetime.now(UTC) - timedelta(days=due_days)
        candidates = self.invoice_repo.list_overdue_candidates(cutoff_date)

        overdue_ids: list[str] = []
        overdue_summaries: list[dict[str, str | float]] = []

        for inv in candidates:
            inv.status = InvoiceStatusEnum.OVERDUE
            self.invoice_repo.update_invoice(inv)
            overdue_ids.append(inv.id)
            overdue_summaries.append(
                {
                    "id": inv.id,
                    "invoice_no": inv.invoice_no,
                    "total_amount": float(inv.total_amount),
                    "invoice_date": inv.invoice_date.isoformat(),
                }
            )

        if overdue_ids and self.audit_repo:
            self.audit_repo.create_log(
                actor_id=current_user.id if current_user else "system",
                action="overdue_invoices_flagged",
                entity_type="invoice",
                entity_id="batch-overdue-scan",
                before_value={"due_window_days": due_days},
                after_value={"flagged_count": len(overdue_ids), "flagged_ids": overdue_ids},
            )


        return OverdueDetectionResponse(
            due_window_days=due_days,
            scanned_count=len(candidates),
            overdue_count=len(overdue_ids),
            overdue_invoice_ids=overdue_ids,
            overdue_invoices=overdue_summaries,
        )

    def _to_payment_response(self, payment: Payment, invoice: Invoice | None = None) -> PaymentResponse:
        inv_no = invoice.invoice_no if invoice else None
        ret_name = None
        if invoice and invoice.sales_order and invoice.sales_order.retailer:
            ret_name = invoice.sales_order.retailer.name

        return PaymentResponse(
            id=payment.id,
            invoice_id=payment.invoice_id,
            invoice_no=inv_no,
            retailer_id=payment.retailer_id,
            retailer_name=ret_name,
            customer_id=payment.customer_id,
            amount=float(payment.amount),
            method=payment.method,
            paid_at=payment.paid_at,
            note=payment.note,
            created_at=payment.created_at or datetime.now(UTC),
        )

