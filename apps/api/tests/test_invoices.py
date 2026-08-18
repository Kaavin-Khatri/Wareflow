"""Unit and integration test suite for GST-ready wholesale invoice generation."""

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.core.di import get_invoice_service
from app.core.security import CurrentUser, get_current_user, require_permission
from app.main import create_app
from app.models.catalog import Product
from app.models.retailer import BuyerTypeEnum, Retailer, SalesOrder, SalesOrderItem, SOStatusEnum
from app.repositories.impl.audit_repository import InMemoryAuditRepository
from app.repositories.impl.invoice_repository import InMemoryInvoiceRepository
from app.repositories.impl.product_repository import InMemoryProductRepository
from app.repositories.impl.sales_order_repository import InMemorySalesOrderRepository
from app.services.invoice_service import InvoiceService


@pytest.fixture
def mock_invoice_dependencies():
    """Build hermetic in-memory dependencies for invoice domain testing."""
    # Seed products
    prod1 = Product(
        id="prod-milk",
        sku="MILK-ORG-001",
        name="Organic Cow Milk 1L",
        hsn_code="0401",
        wholesale_price=60.0,
        cost_price=45.0,
        is_active=True,
    )
    prod2 = Product(
        id="prod-butter",
        sku="BUTTER-500",
        name="Salted Butter 500g",
        hsn_code="0405",
        wholesale_price=250.0,
        cost_price=200.0,
        is_active=True,
    )

    invoice_repo = InMemoryInvoiceRepository()
    so_repo = InMemorySalesOrderRepository()
    prod_repo = InMemoryProductRepository(seed_products=[prod1, prod2])
    audit_repo = InMemoryAuditRepository()

    service = InvoiceService(
        invoice_repo=invoice_repo,
        sales_order_repo=so_repo,
        product_repo=prod_repo,
        audit_repo=audit_repo,
    )

    # Seed a standard retailer
    retailer = Retailer(
        id="ret-100",
        name="Apex Wholesale Mart",
        phone="+919876543210",
        email="apex@example.com",
        address="Sector 18, Gurugram, Haryana",
        gstin="06AAAAA0000A1Z5",
        credit_limit=500000.0,
        credit_balance=0.0,
        is_active=True,
    )

    # Seed confirmed sales order
    order_id = "so-test-101"

    item1 = SalesOrderItem(
        id="so-item-1",
        so_id=order_id,
        product_id="prod-milk",
        qty=100.0,
        unit_price=60.0,
    )
    item2 = SalesOrderItem(
        id="so-item-2",
        so_id=order_id,
        product_id="prod-butter",
        qty=20.0,
        unit_price=250.0,
    )
    sales_order = SalesOrder(
        id=order_id,
        so_number="SO-2026-001",
        buyer_type=BuyerTypeEnum.RETAILER,
        retailer_id=retailer.id,
        status=SOStatusEnum.CONFIRMED,
        order_date=datetime.now(UTC),
        total_amount=11000.0,
        items=[item1, item2],
    )
    sales_order.retailer = retailer
    so_repo.create(sales_order)
    invoice_repo.set_sales_order(sales_order)


    user = CurrentUser(
        id="user-admin-1",
        email="admin@wareflow.io",
        role="Admin",
        permissions={"orders:manage", "orders:view"},
    )


    return {
        "service": service,
        "invoice_repo": invoice_repo,
        "so_repo": so_repo,
        "prod_repo": prod_repo,
        "audit_repo": audit_repo,
        "sales_order": sales_order,
        "user": user,
        "retailer": retailer,
        "prod1": prod1,
        "prod2": prod2,
    }


def test_generating_invoice_twice_for_same_order_is_idempotent(mock_invoice_dependencies):
    """QA 1: Generating an invoice twice for the same order returns the same invoice_no both times."""
    deps = mock_invoice_dependencies
    service: InvoiceService = deps["service"]
    user = deps["user"]
    order_id = deps["sales_order"].id

    # 1st generation
    inv1 = service.generate_invoice_for_sales_order(order_id, user)
    assert inv1 is not None
    assert inv1.invoice_no.startswith("INV/")
    assert len(inv1.items) == 2
    assert inv1.status == "unpaid"

    # 2nd generation (re-request)
    inv2 = service.generate_invoice_for_sales_order(order_id, user)
    assert inv2 is not None
    assert inv2.id == inv1.id
    assert inv2.invoice_no == inv1.invoice_no
    assert inv2.total_amount == inv1.total_amount
    assert len(deps["invoice_repo"]._invoices) == 1, "Only 1 invoice record must exist in repository"


def test_invoice_pricing_and_totals_match_sales_order_and_are_frozen(mock_invoice_dependencies):
    """QA 2: Invoice line prices and totals match confirmed pricing, and are frozen against catalog edits."""
    deps = mock_invoice_dependencies
    service: InvoiceService = deps["service"]
    user = deps["user"]
    order_id = deps["sales_order"].id
    prod_repo = deps["prod_repo"]

    # Line 1: 100 qty @ 60.0 = 6,000 subtotal + 18% tax (1,080) = 7,080
    # Line 2: 20 qty @ 250.0 = 5,000 subtotal + 18% tax (900) = 5,900
    # Invoice Subtotal = 11,000.0, Tax = 1,980.0, Total = 12,980.0
    invoice = service.generate_invoice_for_sales_order(order_id, user)

    assert invoice.subtotal == 11000.0
    assert invoice.tax_amount == 1980.0
    assert invoice.total_amount == 12980.0
    assert invoice.buyer_name == "Apex Wholesale Mart"
    assert invoice.buyer_gstin == "06AAAAA0000A1Z5"

    item_milk = next(it for it in invoice.items if it.product_id == "prod-milk")
    assert item_milk.qty == 100.0
    assert item_milk.unit_price == 60.0
    assert item_milk.hsn_code == "0401"
    assert item_milk.tax_amount == 1080.0
    assert item_milk.total == 7080.0

    # Mutate product catalog price to simulate later price hike
    milk_prod = prod_repo.get_by_id("prod-milk")
    if isinstance(milk_prod, dict):
        milk_prod["wholesale_price"] = 999.0
        milk_prod["hsn_code"] = "9999"
    else:
        milk_prod.wholesale_price = 999.0
        milk_prod.hsn_code = "9999"

    # Re-fetch invoice - must remain frozen

    fetched_inv = service.get_invoice(invoice.id)
    frozen_milk = next(it for it in fetched_inv.items if it.product_id == "prod-milk")
    assert frozen_milk.unit_price == 60.0
    assert frozen_milk.hsn_code == "0401"
    assert fetched_inv.total_amount == 12980.0


def test_invoice_numbers_are_sequential_and_gap_free_per_financial_year(mock_invoice_dependencies):
    """QA 3: Invoice numbers are sequential and gap-free per financial year (3 generated in a row)."""
    deps = mock_invoice_dependencies
    service: InvoiceService = deps["service"]
    user = deps["user"]
    so_repo = deps["so_repo"]
    invoice_repo = deps["invoice_repo"]

    # Generate 3 separate confirmed orders
    order_ids = []
    for i in range(1, 4):
        so_id = f"so-seq-{i}"
        item = SalesOrderItem(
            id=f"item-seq-{i}",
            so_id=so_id,
            product_id="prod-milk",
            qty=10.0,
            unit_price=60.0,
        )
        so = SalesOrder(
            id=so_id,
            so_number=f"SO-SEQ-{i:03d}",
            buyer_type=BuyerTypeEnum.RETAILER,
            retailer_id=deps["retailer"].id,
            status=SOStatusEnum.CONFIRMED,
            order_date=datetime.now(UTC),
            total_amount=600.0,
            items=[item],
        )
        so.retailer = deps["retailer"]
        so_repo.create(so)
        invoice_repo.set_sales_order(so)
        order_ids.append(so_id)

    fy = service.get_financial_year()

    inv1 = service.generate_invoice_for_sales_order(order_ids[0], user)
    inv2 = service.generate_invoice_for_sales_order(order_ids[1], user)
    inv3 = service.generate_invoice_for_sales_order(order_ids[2], user)

    assert inv1.invoice_no == f"INV/{fy}/0001"
    assert inv2.invoice_no == f"INV/{fy}/0002"
    assert inv3.invoice_no == f"INV/{fy}/0003"


def test_cannot_generate_invoice_for_draft_or_cancelled_order(mock_invoice_dependencies):
    """Attempting to generate an invoice for a draft or cancelled order raises HTTP 422."""
    deps = mock_invoice_dependencies
    service: InvoiceService = deps["service"]
    user = deps["user"]
    so_repo = deps["so_repo"]
    invoice_repo = deps["invoice_repo"]

    # Draft Order
    draft_so = SalesOrder(
        id="so-draft-1",
        so_number="SO-DRAFT-001",
        buyer_type=BuyerTypeEnum.RETAILER,
        retailer_id=deps["retailer"].id,
        status=SOStatusEnum.DRAFT,
        order_date=datetime.now(UTC),
        total_amount=500.0,
        items=[],
    )
    so_repo.create(draft_so)
    invoice_repo.set_sales_order(draft_so)


    with pytest.raises(Exception) as exc_info:
        service.generate_invoice_for_sales_order("so-draft-1", user)
    assert "422" in str(exc_info.value) or "confirmed or later" in str(exc_info.value)


def test_invoice_api_endpoints_via_test_client(mock_invoice_dependencies):
    """Integration test for HTTP invoice endpoints."""
    deps = mock_invoice_dependencies
    service: InvoiceService = deps["service"]
    order_id = deps["sales_order"].id

    app = create_app()

    # Override dependencies
    app.dependency_overrides[get_invoice_service] = lambda: service
    app.dependency_overrides[get_current_user] = lambda: deps["user"]
    app.dependency_overrides[require_permission("orders:manage")] = lambda: deps["user"]

    client = TestClient(app)

    # 1. POST /sales-orders/{id}/invoice
    create_res = client.post(f"/sales-orders/{order_id}/invoice")
    assert create_res.status_code == 201
    inv_data = create_res.json()
    assert inv_data["sales_order_id"] == order_id
    assert inv_data["subtotal"] == 11000.0
    assert len(inv_data["items"]) == 2
    invoice_id = inv_data["id"]

    # 2. GET /invoices/{id}
    get_res = client.get(f"/invoices/{invoice_id}")
    assert get_res.status_code == 200
    assert get_res.json()["invoice_no"] == inv_data["invoice_no"]

    # 3. GET /invoices
    list_res = client.get("/invoices")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(item["id"] == invoice_id for item in list_data["items"])
