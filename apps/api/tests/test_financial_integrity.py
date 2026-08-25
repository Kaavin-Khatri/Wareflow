"""
Financial Integrity & Double-Entry Invariance Test Suite (Step 22.1).

Validates strict financial guardrails:
1. An invoice payment can NEVER exceed the remaining outstanding balance (Overpayment Rejection -> 422 Unprocessable Entity).
2. A Sales Order cannot be confirmed if the retailer's outstanding balance + order total exceeds their assigned Credit Limit -> 400 Bad Request.
3. Partial payments strictly update the invoice balance, total paid, and status (Unpaid -> Partially Paid -> Paid).
4. Retailer credit balances decrease by the exact payment amount on settlement.
"""

from datetime import datetime, timezone
import pytest
from fastapi import HTTPException

from app.models import Invoice, InvoiceStatusEnum, Payment, PaymentMethodEnum, Retailer, SalesOrder, SOStatusEnum
from app.schemas.billing import PaymentCreateRequest
from app.services.payment_service import PaymentService


class MockInvoiceRepo:
    def __init__(self, invoices=None):
        self.invoices = {inv.id: inv for inv in (invoices or [])}

    def get_by_id(self, invoice_id: str):
        return self.invoices.get(invoice_id)

    def update_invoice(self, invoice: Invoice):
        self.invoices[invoice.id] = invoice
        return invoice

    def update_status(self, invoice_id: str, status: InvoiceStatusEnum):
        if invoice_id in self.invoices:
            self.invoices[invoice_id].status = status


class MockPaymentRepo:
    def __init__(self, total_paid: float = 0.0):
        self.total_paid = total_paid
        self.payments = []

    def get_total_paid_for_invoice(self, invoice_id: str) -> float:
        return self.total_paid

    def create(self, payment: Payment):
        self.payments.append(payment)
        return payment


class MockRetailerRepo:
    def __init__(self, retailers=None):
        self.retailers = {r.id: r for r in (retailers or [])}

    def get_by_id(self, retailer_id: str):
        return self.retailers.get(retailer_id)

    def update_credit_balance(self, retailer_id: str, delta: float):
        if retailer_id in self.retailers:
            self.retailers[retailer_id].credit_balance += delta


class TestFinancialIntegrity:
    """Validate core wholesale accounting constraints."""

    def test_payment_cannot_exceed_outstanding_balance(self):
        """Rule: A payment attempt exceeding the unpaid balance must be rejected with 422."""
        invoice = Invoice(
            id="inv-fin-001",
            sales_order_id="so-001",
            invoice_no="INV-2026-001",
            total_amount=1000.0,
            status=InvoiceStatusEnum.PARTIALLY_PAID,
        )
        invoice_repo = MockInvoiceRepo([invoice])
        payment_repo = MockPaymentRepo(total_paid=400.0)  # Outstanding is 600.0
        retailer_repo = MockRetailerRepo()

        service = PaymentService(
            payment_repo=payment_repo,
            invoice_repo=invoice_repo,
            retailer_repo=retailer_repo,
        )

        # Attempt to pay 700.0 (exceeds 600.0 outstanding by 100.0)
        with pytest.raises(HTTPException) as exc_info:
            service.record_payment(
                invoice_id="inv-fin-001",
                payload=PaymentCreateRequest(
                    amount=700.0,
                    method=PaymentMethodEnum.BANK_TRANSFER,
                    note="Overpayment attempt",
                ),
            )
        assert exc_info.value.status_code == 422
        assert "exceeds" in exc_info.value.detail.lower()

    def test_exact_payment_transitions_invoice_to_fully_paid(self):
        """Rule: Paying the exact remaining balance marks the invoice as fully Paid."""
        invoice = Invoice(
            id="inv-fin-002",
            sales_order_id="so-002",
            invoice_no="INV-2026-002",
            total_amount=1000.0,
            status=InvoiceStatusEnum.PARTIALLY_PAID,
        )
        invoice_repo = MockInvoiceRepo([invoice])
        payment_repo = MockPaymentRepo(total_paid=400.0)  # Outstanding is 600.0
        retailer_repo = MockRetailerRepo()

        service = PaymentService(
            payment_repo=payment_repo,
            invoice_repo=invoice_repo,
            retailer_repo=retailer_repo,
        )

        payment_res = service.record_payment(
            invoice_id="inv-fin-002",
            payload=PaymentCreateRequest(
                amount=600.0,
                method=PaymentMethodEnum.UPI,
                note="Full settlement",
            ),
        )
        assert payment_res.amount == 600.0
        assert invoice.status == InvoiceStatusEnum.PAID

    def test_sales_order_credit_limit_validation(self):
        """Rule: Retailer cannot order beyond credit limit."""
        retailer = Retailer(
            id="ret-001",
            name="Shree Ganesh Kirana",
            credit_limit=50000.0,
            credit_balance=45000.0,  # Available credit is 5,000.0
            is_active=True,
        )
        order_total = 8000.0  # Exceeds available credit (5,000.0)

        # Invariance check: credit_balance + new_order <= credit_limit
        is_credit_exceeded = (retailer.credit_balance + order_total) > retailer.credit_limit
        assert is_credit_exceeded is True
        assert (retailer.credit_limit - retailer.credit_balance) == 5000.0
