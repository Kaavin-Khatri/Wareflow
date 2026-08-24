"""Unit and Integration tests for Accounts-Receivable (AR) Aging Report (Step 15.2).

Verifies 30/60/90-day aging bucket boundaries, hand-calculated mixed-age invoices,
zero-balance handling, and the GET /analytics/ar-aging endpoint.
"""

from datetime import UTC, date, datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.core.di import get_ar_aging_service
from app.core.security import CurrentUser, get_current_user
from app.main import app
from app.models.billing import Invoice, InvoiceStatusEnum, Payment, PaymentMethodEnum
from app.models.retailer import BuyerTypeEnum, Retailer, SalesOrder, SOStatusEnum
from app.repositories.impl.invoice_repository import InMemoryInvoiceRepository
from app.repositories.impl.retailer_repository import InMemoryRetailerRepository
from app.services.ar_aging_service import ARAgingService


@pytest.fixture
def retailer_repo() -> InMemoryRetailerRepository:
    return InMemoryRetailerRepository()


@pytest.fixture
def invoice_repo() -> InMemoryInvoiceRepository:
    return InMemoryInvoiceRepository()


@pytest.fixture
def ar_aging_service(
    invoice_repo: InMemoryInvoiceRepository,
    retailer_repo: InMemoryRetailerRepository,
) -> ARAgingService:
    return ARAgingService(
        invoice_repository=invoice_repo,
        retailer_repository=retailer_repo,
    )


def test_ar_aging_fresh_deployment_empty_state(ar_aging_service: ARAgingService) -> None:
    """Fresh deployment with zero retailers returns clean zeroed summary."""
    report = ar_aging_service.get_ar_aging_report(as_of=date(2026, 8, 24))

    assert report.as_of_date == "2026-08-24"
    assert report.summary.total_outstanding == 0.0
    assert report.summary.total_overdue == 0.0
    assert report.summary.total_current == 0.0
    assert report.summary.total_bucket_1_30 == 0.0
    assert report.summary.total_bucket_31_60 == 0.0
    assert report.summary.total_bucket_61_90 == 0.0
    assert report.summary.total_bucket_90_plus == 0.0
    assert report.summary.total_retailers == 0
    assert report.summary.overdue_retailers_count == 0
    assert report.retailers == []


def test_ar_aging_exact_bucket_calculations_qa_scenario(
    ar_aging_service: ARAgingService,
    retailer_repo: InMemoryRetailerRepository,
    invoice_repo: InMemoryInvoiceRepository,
) -> None:
    """
    QA Checklist Verification:
    1. Bucket totals match hand-computed checks for 2 retailers with mixed-age invoices.
    2. Retailers with zero outstanding balance are clearly zeroed when included, or excluded via toggle.
    """
    as_of = date(2026, 8, 24)

    # 1. Setup Retailers
    r1 = Retailer(
        id="ret-1",
        name="Vashi APMC Wholesale Traders",
        contact_person="Ramesh Patel",
        phone="+919820011223",
        credit_limit=500000.0,
        credit_balance=215000.0,
        is_active=True,
    )
    r2 = Retailer(
        id="ret-2",
        name="Surat Agro Mart",
        contact_person="Kiran Shah",
        phone="+919820044556",
        credit_limit=300000.0,
        credit_balance=150000.0,
        is_active=True,
    )
    r3 = Retailer(
        id="ret-3",
        name="Pune Zero Balance Retailers",
        contact_person="Anil Deshmukh",
        phone="+919820077889",
        credit_limit=200000.0,
        credit_balance=0.0,
        is_active=True,
    )
    retailer_repo.create(r1)
    retailer_repo.create(r2)
    retailer_repo.create(r3)

    # 2. Setup Sales Orders for SO linkage
    so1 = SalesOrder(
        id="so-1",
        so_number="SO-101",
        retailer_id="ret-1",
        buyer_type=BuyerTypeEnum.RETAILER,
        status=SOStatusEnum.DELIVERED,
        total_amount=100000.0,
    )
    so2 = SalesOrder(
        id="so-2",
        so_number="SO-102",
        retailer_id="ret-1",
        buyer_type=BuyerTypeEnum.RETAILER,
        status=SOStatusEnum.DELIVERED,
        total_amount=50000.0,
    )
    so3 = SalesOrder(
        id="so-3",
        so_number="SO-103",
        retailer_id="ret-1",
        buyer_type=BuyerTypeEnum.RETAILER,
        status=SOStatusEnum.DELIVERED,
        total_amount=75000.0,
    )
    so4 = SalesOrder(
        id="so-4",
        so_number="SO-201",
        retailer_id="ret-2",
        buyer_type=BuyerTypeEnum.RETAILER,
        status=SOStatusEnum.DELIVERED,
        total_amount=60000.0,
    )
    so5 = SalesOrder(
        id="so-5",
        so_number="SO-202",
        retailer_id="ret-2",
        buyer_type=BuyerTypeEnum.RETAILER,
        status=SOStatusEnum.DELIVERED,
        total_amount=90000.0,
    )
    so6 = SalesOrder(
        id="so-6",
        so_number="SO-203",
        retailer_id="ret-2",
        buyer_type=BuyerTypeEnum.RETAILER,
        status=SOStatusEnum.DELIVERED,
        total_amount=30000.0,
    )
    for so in (so1, so2, so3, so4, so5, so6):
        invoice_repo.set_sales_order(so)

    # 3. Setup Mixed-Age Invoices
    # Retailer 1:
    # Inv 1: Future due date (2026-08-25) -> Current: 100,000
    inv1 = Invoice(
        id="inv-101",
        sales_order_id="so-1",
        invoice_no="INV/2026-27/0101",
        invoice_date=datetime(2026, 7, 26, 10, 0, tzinfo=UTC),
        total_amount=100000.0,
        status=InvoiceStatusEnum.UNPAID,
    )
    inv1.due_date = date(2026, 8, 25)  # 1 day in future
    inv1.sales_order = so1

    # Inv 2: Due 2026-08-10 (14 days overdue) with partial payment 10,000 -> 1-30 Days: 40,000
    inv2 = Invoice(
        id="inv-102",
        sales_order_id="so-2",
        invoice_no="INV/2026-27/0102",
        invoice_date=datetime(2026, 7, 11, 10, 0, tzinfo=UTC),
        total_amount=50000.0,
        status=InvoiceStatusEnum.PARTIALLY_PAID,
    )
    inv2.due_date = date(2026, 8, 10)
    inv2.payments = [
        Payment(
            id="pay-1",
            invoice_id="inv-102",
            retailer_id="ret-1",
            amount=10000.0,
            method=PaymentMethodEnum.UPI,
            paid_at=datetime(2026, 8, 15, 10, 0, tzinfo=UTC),
        )
    ]
    inv2.sales_order = so2

    # Inv 3: Due 2026-07-10 (45 days overdue) -> 31-60 Days: 75,000
    inv3 = Invoice(
        id="inv-103",
        sales_order_id="so-3",
        invoice_no="INV/2026-27/0103",
        invoice_date=datetime(2026, 6, 10, 10, 0, tzinfo=UTC),
        total_amount=75000.0,
        status=InvoiceStatusEnum.OVERDUE,
    )
    inv3.due_date = date(2026, 7, 10)
    inv3.sales_order = so3

    # Retailer 2:
    # Inv 4: Due 2026-06-10 (75 days overdue) -> 61-90 Days: 60,000
    inv4 = Invoice(
        id="inv-201",
        sales_order_id="so-4",
        invoice_no="INV/2026-27/0201",
        invoice_date=datetime(2026, 5, 11, 10, 0, tzinfo=UTC),
        total_amount=60000.0,
        status=InvoiceStatusEnum.OVERDUE,
    )
    inv4.due_date = date(2026, 6, 10)
    inv4.sales_order = so4

    # Inv 5: Due 2026-04-15 (131 days overdue) -> 90+ Days: 90,000
    inv5 = Invoice(
        id="inv-202",
        sales_order_id="so-5",
        invoice_no="INV/2026-27/0202",
        invoice_date=datetime(2026, 3, 16, 10, 0, tzinfo=UTC),
        total_amount=90000.0,
        status=InvoiceStatusEnum.OVERDUE,
    )
    inv5.due_date = date(2026, 4, 15)
    inv5.sales_order = so5

    # Inv 6: Fully Paid (total 30,000, paid 30,000) -> Excluded from outstanding AR
    inv6 = Invoice(
        id="inv-203",
        sales_order_id="so-6",
        invoice_no="INV/2026-27/0203",
        invoice_date=datetime(2026, 1, 1, 10, 0, tzinfo=UTC),
        total_amount=30000.0,
        status=InvoiceStatusEnum.PAID,
    )
    inv6.due_date = date(2026, 1, 31)
    inv6.paid_amount = 30000.0
    inv6.sales_order = so6

    for inv in (inv1, inv2, inv3, inv4, inv5, inv6):
        invoice_repo.create_invoice(inv, [])

    # Execute Report with include_zero_balance=True
    report = ar_aging_service.get_ar_aging_report(include_zero_balance=True, as_of=as_of)

    # 4. Verify Retailer 1 Breakdown
    r1_item = next(item for item in report.retailers if item.retailer_id == "ret-1")
    assert r1_item.retailer_name == "Vashi APMC Wholesale Traders"
    assert r1_item.current == 100000.0
    assert r1_item.bucket_1_30 == 40000.0
    assert r1_item.bucket_31_60 == 75000.0
    assert r1_item.bucket_61_90 == 0.0
    assert r1_item.bucket_90_plus == 0.0
    assert r1_item.total_overdue == 115000.0
    assert r1_item.total_outstanding == 215000.0
    assert r1_item.invoice_count == 3
    assert r1_item.oldest_invoice_date == "2026-06-10"

    # 5. Verify Retailer 2 Breakdown
    r2_item = next(item for item in report.retailers if item.retailer_id == "ret-2")
    assert r2_item.retailer_name == "Surat Agro Mart"
    assert r2_item.current == 0.0
    assert r2_item.bucket_1_30 == 0.0
    assert r2_item.bucket_31_60 == 0.0
    assert r2_item.bucket_61_90 == 60000.0
    assert r2_item.bucket_90_plus == 90000.0
    assert r2_item.total_overdue == 150000.0
    assert r2_item.total_outstanding == 150000.0
    assert r2_item.invoice_count == 2
    assert r2_item.oldest_invoice_date == "2026-03-16"

    # 6. Verify Retailer 3 (Zero Balance) is clearly zeroed, not missing
    r3_item = next(item for item in report.retailers if item.retailer_id == "ret-3")
    assert r3_item.retailer_name == "Pune Zero Balance Retailers"
    assert r3_item.current == 0.0
    assert r3_item.bucket_1_30 == 0.0
    assert r3_item.bucket_31_60 == 0.0
    assert r3_item.bucket_61_90 == 0.0
    assert r3_item.bucket_90_plus == 0.0
    assert r3_item.total_overdue == 0.0
    assert r3_item.total_outstanding == 0.0
    assert r3_item.invoice_count == 0

    # 7. Verify Sorting: Retailer 2 has highest total_overdue (150,000 > 115,000 > 0)
    assert report.retailers[0].retailer_id == "ret-2"
    assert report.retailers[1].retailer_id == "ret-1"
    assert report.retailers[2].retailer_id == "ret-3"

    # 8. Verify Portfolio Summary
    assert report.summary.total_current == 100000.0
    assert report.summary.total_bucket_1_30 == 40000.0
    assert report.summary.total_bucket_31_60 == 75000.0
    assert report.summary.total_bucket_61_90 == 60000.0
    assert report.summary.total_bucket_90_plus == 90000.0
    assert report.summary.total_overdue == 265000.0
    assert report.summary.total_outstanding == 365000.0
    assert report.summary.total_retailers == 3
    assert report.summary.overdue_retailers_count == 2

    # 9. Verify include_zero_balance=False excludes zero balance retailers
    filtered_report = ar_aging_service.get_ar_aging_report(
        include_zero_balance=False, as_of=as_of
    )
    assert len(filtered_report.retailers) == 2
    assert all(item.retailer_id != "ret-3" for item in filtered_report.retailers)


def test_ar_aging_api_endpoint(ar_aging_service: ARAgingService) -> None:
    """FastAPI TestClient verifies GET /analytics/ar-aging with permission guard."""
    mock_user = CurrentUser(
        id="usr-owner-1",
        email="owner@wareflow.in",
        role="owner",
        permissions={"invoices:view"},
    )
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_ar_aging_service] = lambda: ar_aging_service

    client = TestClient(app)
    response = client.get("/analytics/ar-aging?include_zero_balance=true")
    assert response.status_code == 200
    data = response.json()
    assert "as_of_date" in data
    assert "summary" in data
    assert "retailers" in data

    app.dependency_overrides.clear()
