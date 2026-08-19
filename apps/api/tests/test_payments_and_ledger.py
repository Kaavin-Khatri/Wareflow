"""Automated tests for Payments, Accounts-Receivable Ledger, and Overdue Detection."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.di import get_invoice_service, get_ledger_service, get_payment_service
from app.core.security import CurrentUser, get_current_user, require_permission
from app.main import create_app
from app.models.billing import Invoice, InvoiceStatusEnum, PaymentMethodEnum
from app.models.retailer import BuyerTypeEnum, Retailer, SalesOrder, SOStatusEnum
from app.repositories.impl.audit_repository import InMemoryAuditRepository
from app.repositories.impl.invoice_repository import InMemoryInvoiceRepository
from app.repositories.impl.payment_repository import InMemoryPaymentRepository
from app.repositories.impl.product_repository import InMemoryProductRepository
from app.repositories.impl.retailer_repository import InMemoryRetailerRepository
from app.repositories.impl.sales_order_repository import InMemorySalesOrderRepository
from app.schemas.billing import PaymentCreateRequest
from app.services.invoice_service import InvoiceService
from app.services.ledger_service import LedgerService
from app.services.payment_service import PaymentService


@pytest.fixture
def mock_billing_environment():
    """Build hermetic in-memory test environment for billing, payments, and AR ledger."""
    audit_repo = InMemoryAuditRepository()
    invoice_repo = InMemoryInvoiceRepository()
    payment_repo = InMemoryPaymentRepository()
    so_repo = InMemorySalesOrderRepository()
    retailer_repo = InMemoryRetailerRepository()
    prod_repo = InMemoryProductRepository()

    invoice_service = InvoiceService(
        invoice_repo=invoice_repo,
        sales_order_repo=so_repo,
        product_repo=prod_repo,
        audit_repo=audit_repo,
        payment_repo=payment_repo,
    )
    payment_service = PaymentService(
        payment_repo=payment_repo,
        invoice_repo=invoice_repo,
        retailer_repo=retailer_repo,
        audit_repo=audit_repo,
    )
    ledger_service = LedgerService(
        retailer_repo=retailer_repo,
        invoice_repo=invoice_repo,
        payment_repo=payment_repo,
    )

    user = CurrentUser(
        id="user-fin-admin",
        email="finance@wareflow.io",
        role="Admin",
        permissions={"orders:manage", "orders:view", "settings:manage"},
    )

    return {
        "invoice_repo": invoice_repo,
        "payment_repo": payment_repo,
        "so_repo": so_repo,
        "retailer_repo": retailer_repo,
        "invoice_service": invoice_service,
        "payment_service": payment_service,
        "ledger_service": ledger_service,
        "audit_repo": audit_repo,
        "user": user,
    }


def _seed_retailer_and_confirmed_invoice(
    env: dict,
    retailer_id: str,
    retailer_name: str,
    invoice_no: str,
    total_amount: float,
    days_ago: int = 0,
) -> tuple[Retailer, Invoice]:
    """Helper to seed a retailer and an invoice."""
    retailer_repo: InMemoryRetailerRepository = env["retailer_repo"]
    so_repo: InMemorySalesOrderRepository = env["so_repo"]
    invoice_repo: InMemoryInvoiceRepository = env["invoice_repo"]

    retailer = retailer_repo.get_by_id(retailer_id)
    if not retailer:
        retailer = Retailer(
            id=retailer_id,
            name=retailer_name,
            phone="+919876543210",
            email=f"{retailer_id}@retail.com",
            address="Trade Hub, New Delhi",
            gstin="07AAAAA1234A1Z5",
            credit_limit=500000.0,
            credit_balance=total_amount,
            is_active=True,
        )
        retailer_repo.create(retailer)
    else:
        current_bal = float(retailer.credit_balance or 0.0)
        retailer_repo.update(retailer_id, {"credit_balance": current_bal + total_amount})
        retailer = retailer_repo.get_by_id(retailer_id)

    so_id = f"so-{uuid.uuid4().hex[:8]}"
    so = SalesOrder(
        id=so_id,
        so_number=f"SO-{invoice_no[-4:]}",
        buyer_type=BuyerTypeEnum.RETAILER,
        retailer_id=retailer.id,
        status=SOStatusEnum.CONFIRMED,
        order_date=datetime.now(UTC) - timedelta(days=days_ago),
        total_amount=total_amount,
        items=[],
    )
    so.retailer = retailer
    so_repo.create(so)
    invoice_repo.set_sales_order(so)

    inv_date = datetime.now(UTC) - timedelta(days=days_ago)
    invoice = Invoice(
        id=f"inv-{uuid.uuid4().hex[:8]}",
        sales_order_id=so.id,
        invoice_no=invoice_no,
        invoice_date=inv_date,
        gst_rate=18.0,
        subtotal=round(total_amount / 1.18, 2),
        tax_amount=round(total_amount - (total_amount / 1.18), 2),
        total_amount=total_amount,
        status=InvoiceStatusEnum.UNPAID,
        created_at=inv_date,
    )
    invoice.sales_order = so
    invoice_repo.create_invoice(invoice, [])
    return retailer, invoice


def test_recording_payment_updates_invoice_status_at_each_threshold(mock_billing_environment):
    """QA 1: Recording partial payment -> partially_paid; full payment -> paid; credit_balance decreases."""
    env = mock_billing_environment
    payment_service: PaymentService = env["payment_service"]
    invoice_repo: InMemoryInvoiceRepository = env["invoice_repo"]
    retailer_repo: InMemoryRetailerRepository = env["retailer_repo"]
    user = env["user"]

    retailer, invoice = _seed_retailer_and_confirmed_invoice(
        env, "ret-qa-1", "Apex Superstore", "INV/2026-27/0010", 10000.0
    )

    assert float(retailer.credit_balance) == 10000.0
    assert invoice.status == InvoiceStatusEnum.UNPAID

    # 1. Partial payment: ₹4,000
    p1 = payment_service.record_payment(
        invoice_id=invoice.id,
        payload=PaymentCreateRequest(
            amount=4000.0,
            method=PaymentMethodEnum.UPI,
            note="Partial payment batch 1",
        ),
        current_user=user,
    )

    assert p1.amount == 4000.0
    updated_inv = invoice_repo.get_by_id(invoice.id)
    assert updated_inv.status == InvoiceStatusEnum.PARTIALLY_PAID

    updated_ret = retailer_repo.get_by_id(retailer.id)
    assert float(updated_ret.credit_balance) == 6000.0

    # 2. Remainder payment: ₹6,000 -> full settlement
    p2 = payment_service.record_payment(
        invoice_id=invoice.id,
        payload=PaymentCreateRequest(
            amount=6000.0,
            method=PaymentMethodEnum.BANK_TRANSFER,
            note="Final settlement NEFT-9988",
        ),
        current_user=user,
    )

    assert p2.amount == 6000.0
    final_inv = invoice_repo.get_by_id(invoice.id)
    assert final_inv.status == InvoiceStatusEnum.PAID

    final_ret = retailer_repo.get_by_id(retailer.id)
    assert float(final_ret.credit_balance) == 0.0


def test_overpaying_an_invoice_is_blocked_with_clear_message(mock_billing_environment):
    """QA 3: Overpaying an invoice is blocked with HTTP 422 stating the exact outstanding balance."""
    env = mock_billing_environment
    payment_service: PaymentService = env["payment_service"]
    user = env["user"]

    _, invoice = _seed_retailer_and_confirmed_invoice(
        env, "ret-qa-overpay", "Daily Mart", "INV/2026-27/0020", 10000.0
    )

    # Partial payment of 4,000 leaves outstanding balance of 6,000
    payment_service.record_payment(
        invoice_id=invoice.id,
        payload=PaymentCreateRequest(amount=4000.0, method=PaymentMethodEnum.CASH),
        current_user=user,
    )

    # Attempting to pay ₹6,001 or ₹7,000 must be rejected
    with pytest.raises(Exception) as exc_info:
        payment_service.record_payment(
            invoice_id=invoice.id,
            payload=PaymentCreateRequest(amount=7000.0, method=PaymentMethodEnum.CASH),
            current_user=user,
        )

    err_str = str(exc_info.value)
    assert "422" in err_str or "exceeds" in err_str
    assert "6,000.00" in err_str or "6000" in err_str


def test_retailer_ledger_running_balance_matches_stored_credit_balance_exactly(
    mock_billing_environment,
):
    """QA 2: Verify AR ledger running balance matches credit_balance exactly for 2 retailers with mixed transactions."""
    env = mock_billing_environment
    payment_service: PaymentService = env["payment_service"]
    ledger_service: LedgerService = env["ledger_service"]
    retailer_repo: InMemoryRetailerRepository = env["retailer_repo"]
    user = env["user"]

    # --- Retailer 1: Fresh Wholesale ---
    ret1, inv1_1 = _seed_retailer_and_confirmed_invoice(
        env, "ret-ledger-1", "Fresh Wholesale", "INV/2026-27/0031", 15000.0, days_ago=10
    )
    _, inv1_2 = _seed_retailer_and_confirmed_invoice(
        env, "ret-ledger-1", "Fresh Wholesale", "INV/2026-27/0032", 25000.0, days_ago=5
    )

    # Invoiced total = 40,000. Record payments:
    payment_service.record_payment(
        invoice_id=inv1_1.id,
        payload=PaymentCreateRequest(
            amount=10000.0,
            method=PaymentMethodEnum.BANK_TRANSFER,
            paid_at=datetime.now(UTC) - timedelta(days=7),
            note="Partial on Inv 31",
        ),
        current_user=user,
    )
    payment_service.record_payment(
        invoice_id=inv1_2.id,
        payload=PaymentCreateRequest(
            amount=12500.0,
            method=PaymentMethodEnum.UPI,
            paid_at=datetime.now(UTC) - timedelta(days=2),
            note="50% on Inv 32",
        ),
        current_user=user,
    )

    # Expected remaining balance = 15,000 + 25,000 - 10,000 - 12,500 = 17,500
    ledger1 = ledger_service.get_retailer_ledger("ret-ledger-1")
    stored_ret1 = retailer_repo.get_by_id("ret-ledger-1")

    assert len(ledger1.entries) == 4
    assert ledger1.total_invoiced == 40000.0
    assert ledger1.total_paid == 22500.0
    assert ledger1.current_credit_balance == 17500.0
    assert float(stored_ret1.credit_balance) == 17500.0
    assert ledger1.entries[-1].running_balance == 17500.0
    assert ledger1.entries[-1].running_balance == float(stored_ret1.credit_balance)

    # --- Retailer 2: Green Agro Mart ---
    ret2, inv2_1 = _seed_retailer_and_confirmed_invoice(
        env, "ret-ledger-2", "Green Agro Mart", "INV/2026-27/0041", 50000.0, days_ago=20
    )
    payment_service.record_payment(
        invoice_id=inv2_1.id,
        payload=PaymentCreateRequest(
            amount=50000.0,
            method=PaymentMethodEnum.CHEQUE,
            paid_at=datetime.now(UTC) - timedelta(days=15),
            note="Cheque CHQ-10029",
        ),
        current_user=user,
    )
    _, inv2_2 = _seed_retailer_and_confirmed_invoice(
        env, "ret-ledger-2", "Green Agro Mart", "INV/2026-27/0042", 30000.0, days_ago=4
    )

    # Expected remaining balance = 50,000 - 50,000 + 30,000 = 30,000
    ledger2 = ledger_service.get_retailer_ledger("ret-ledger-2")
    stored_ret2 = retailer_repo.get_by_id("ret-ledger-2")

    assert len(ledger2.entries) == 3
    assert ledger2.total_invoiced == 80000.0
    assert ledger2.total_paid == 50000.0
    assert ledger2.current_credit_balance == 30000.0
    assert float(stored_ret2.credit_balance) == 30000.0
    assert ledger2.entries[-1].running_balance == 30000.0
    assert ledger2.entries[-1].running_balance == float(stored_ret2.credit_balance)


def test_invoice_past_due_date_with_no_full_payment_flips_to_overdue(mock_billing_environment):
    """QA 4: Invoice older than the due-window (default 30 days) transitions to overdue."""
    env = mock_billing_environment
    payment_service: PaymentService = env["payment_service"]
    invoice_repo: InMemoryInvoiceRepository = env["invoice_repo"]
    user = env["user"]

    # Invoice 1: 45 days old, unpaid -> Should flip to overdue
    _, inv_old = _seed_retailer_and_confirmed_invoice(
        env, "ret-overdue", "Century Store", "INV/2026-27/0051", 20000.0, days_ago=45
    )
    # Invoice 2: 10 days old, unpaid -> Should remain unpaid
    _, inv_recent = _seed_retailer_and_confirmed_invoice(
        env, "ret-overdue", "Century Store", "INV/2026-27/0052", 15000.0, days_ago=10
    )

    scan_result = payment_service.detect_overdue_invoices(due_days=30, current_user=user)

    assert scan_result.overdue_count >= 1
    assert inv_old.id in scan_result.overdue_invoice_ids

    checked_old = invoice_repo.get_by_id(inv_old.id)
    checked_recent = invoice_repo.get_by_id(inv_recent.id)

    assert checked_old.status == InvoiceStatusEnum.OVERDUE
    assert checked_recent.status == InvoiceStatusEnum.UNPAID


def test_payment_and_ledger_api_endpoints_via_test_client(mock_billing_environment):
    """Integration test for HTTP payment, ledger statement, and overdue endpoints."""
    env = mock_billing_environment
    invoice_service: InvoiceService = env["invoice_service"]
    payment_service: PaymentService = env["payment_service"]
    ledger_service: LedgerService = env["ledger_service"]

    retailer, invoice = _seed_retailer_and_confirmed_invoice(
        env, "ret-api-test", "Metro Wholesale", "INV/2026-27/0061", 20000.0
    )

    app = create_app()
    app.dependency_overrides[get_invoice_service] = lambda: invoice_service
    app.dependency_overrides[get_payment_service] = lambda: payment_service
    app.dependency_overrides[get_ledger_service] = lambda: ledger_service
    app.dependency_overrides[get_current_user] = lambda: env["user"]
    app.dependency_overrides[require_permission("orders:manage")] = lambda: env["user"]

    client = TestClient(app)

    # 1. POST /invoices/{id}/payments
    pay_res = client.post(
        f"/invoices/{invoice.id}/payments",
        json={
            "amount": 8000.0,
            "method": "upi",
            "note": "Advance UPI transfer",
        },
    )
    assert pay_res.status_code == 201, pay_res.text
    pay_data = pay_res.json()
    assert pay_data["amount"] == 8000.0

    # 2. GET /invoices/{id}/payments
    list_pay_res = client.get(f"/invoices/{invoice.id}/payments")
    assert list_pay_res.status_code == 200
    assert len(list_pay_res.json()) == 1

    # 3. GET /retailers/{id}/ledger
    ledger_res = client.get(f"/retailers/{retailer.id}/ledger")
    assert ledger_res.status_code == 200
    ledger_data = ledger_res.json()
    assert ledger_data["retailer_id"] == retailer.id
    assert ledger_data["total_invoiced"] == 20000.0
    assert ledger_data["total_paid"] == 8000.0
    assert ledger_data["current_credit_balance"] == 12000.0
    assert len(ledger_data["entries"]) == 2

    # 4. POST /invoices/detect-overdue
    overdue_res = client.post("/invoices/detect-overdue?due_days=30")
    assert overdue_res.status_code == 200
    assert "overdue_count" in overdue_res.json()
