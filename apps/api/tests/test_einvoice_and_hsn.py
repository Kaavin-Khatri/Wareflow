"""Automated tests for Step 10.3: GST Compliance, HSN Code Validation, E-Invoice & E-Way Bill."""

import uuid
from datetime import UTC, datetime

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.security import CurrentUser, get_current_user, require_permission
from app.main import create_app
from app.models.audit_and_settings import BusinessSettings
from app.models.billing import Invoice, InvoiceItem, InvoiceStatusEnum
from app.models.retailer import BuyerTypeEnum, SalesOrder, SalesOrderItem, SOStatusEnum
from app.repositories.impl.audit_repository import InMemoryAuditRepository
from app.repositories.impl.business_settings_repository import (
    InMemoryBusinessSettingsRepository,
)
from app.repositories.impl.invoice_repository import InMemoryInvoiceRepository
from app.repositories.impl.product_repository import InMemoryProductRepository
from app.repositories.impl.sales_order_repository import InMemorySalesOrderRepository
from app.schemas.billing import EWayBillGenerateRequest
from app.services.einvoice_service import EinvoiceService, SandboxGspProvider
from app.services.invoice_service import InvoiceService


@pytest.fixture
def test_user() -> CurrentUser:
    """Fixture for authenticated admin/accountant user."""
    return CurrentUser(
        id="usr-gst-admin",
        email="admin@wareflow.io",
        role="Admin",
        permissions={
            "orders:view",
            "orders:manage",
            "invoices:view",
            "invoices:manage",
            "retailers:view",
        },
    )


def test_missing_hsn_code_blocks_invoice_generation_with_clear_error(test_user: CurrentUser):
    """Attempting to invoice a product with no/empty HSN code is blocked with 422 and names the product."""
    product_repo = InMemoryProductRepository()
    sales_order_repo = InMemorySalesOrderRepository()
    invoice_repo = InMemoryInvoiceRepository()
    audit_repo = InMemoryAuditRepository()

    # Create product without HSN code
    product_no_hsn = {
        "id": "prod-no-hsn-1",
        "name": "Artisan Goat Cheese 200g",
        "sku": "DAIRY-CHEESE-001",
        "category_id": "cat-dairy",
        "unit_of_measure": "PIECE",
        "wholesale_price": 350.0,
        "cost_price": 220.0,
        "tax_rate": 18.0,
        "hsn_code": None,  # Missing HSN!
        "is_active": True,
    }
    product_repo._products["prod-no-hsn-1"] = product_no_hsn

    so = SalesOrder(
        id="so-hsn-check-1",
        so_number="SO-2026-9901",
        order_date=datetime.now(UTC),
        buyer_type=BuyerTypeEnum.RETAILER,
        retailer_id="ret-1",
        status=SOStatusEnum.CONFIRMED,
        total_amount=826.0,
        items=[
            SalesOrderItem(
                id="so-item-1",
                so_id="so-hsn-check-1",
                product_id="prod-no-hsn-1",
                qty=2.0,
                unit_price=350.0,
            )
        ],
    )
    sales_order_repo.create(so)
    invoice_repo.set_sales_order(so)

    invoice_service = InvoiceService(
        invoice_repo=invoice_repo,
        sales_order_repo=sales_order_repo,
        product_repo=product_repo,
        audit_repo=audit_repo,
    )

    with pytest.raises(HTTPException) as exc_info:
        invoice_service.generate_invoice_for_sales_order("so-hsn-check-1", test_user)

    assert exc_info.value.status_code == 422
    assert "missing a mandatory HSN code" in exc_info.value.detail
    assert "Artisan Goat Cheese 200g" in exc_info.value.detail
    assert "DAIRY-CHEESE-001" in exc_info.value.detail


def test_products_with_valid_hsn_generate_tax_invoice_with_frozen_hsn(test_user: CurrentUser):
    """Invoicing products with valid HSN codes succeeds and captures HSN code snapshot."""
    product_repo = InMemoryProductRepository()
    sales_order_repo = InMemorySalesOrderRepository()
    invoice_repo = InMemoryInvoiceRepository()
    audit_repo = InMemoryAuditRepository()

    product_with_hsn = {
        "id": "prod-valid-hsn-1",
        "name": "Pasteurized Milk 1L",
        "sku": "DAIRY-MILK-1L",
        "category_id": "cat-dairy",
        "unit_of_measure": "PACK",
        "wholesale_price": 60.0,
        "cost_price": 45.0,
        "tax_rate": 18.0,
        "hsn_code": "04012000",
        "is_active": True,
    }
    product_repo._products["prod-valid-hsn-1"] = product_with_hsn

    so = SalesOrder(
        id="so-hsn-check-2",
        so_number="SO-2026-9902",
        order_date=datetime.now(UTC),
        buyer_type=BuyerTypeEnum.RETAILER,
        retailer_id="ret-1",
        status=SOStatusEnum.CONFIRMED,
        total_amount=708.0,
        items=[
            SalesOrderItem(
                id="so-item-2",
                so_id="so-hsn-check-2",
                product_id="prod-valid-hsn-1",
                qty=10.0,
                unit_price=60.0,
            )
        ],
    )
    sales_order_repo.create(so)
    invoice_repo.set_sales_order(so)

    invoice_service = InvoiceService(
        invoice_repo=invoice_repo,
        sales_order_repo=sales_order_repo,
        product_repo=product_repo,
        audit_repo=audit_repo,
    )

    inv = invoice_service.generate_invoice_for_sales_order("so-hsn-check-2", test_user)
    assert inv.items[0].hsn_code == "04012000"


def test_sandbox_einvoice_generates_valid_64_hex_irn_and_qr_code(test_user: CurrentUser):
    """With GSP sandbox provider, an e-invoice generates valid statutory 64-hex IRN and signed QR code."""
    invoice_repo = InMemoryInvoiceRepository()
    business_repo = InMemoryBusinessSettingsRepository(
        initial_settings=BusinessSettings(
            id=str(uuid.uuid4()),
            business_name="Wareflow Distribution India LLP",
            gstin="07AAAAA1234A1Z5",
            fssai_license_no="10019011000123",
        )
    )
    audit_repo = InMemoryAuditRepository()

    now = datetime.now(UTC)
    invoice = Invoice(
        id="inv-irn-test-1",
        invoice_no="INV/2026-27/0055",
        invoice_date=now,
        gst_rate=18.0,
        subtotal=50000.0,
        tax_amount=9000.0,
        total_amount=59000.0,
        status=InvoiceStatusEnum.UNPAID,
        created_at=now,
    )
    items = [
        InvoiceItem(
            id="item-irn-1",
            invoice_id="inv-irn-test-1",
            product_id="prod-1",
            product_name="Pure Desi Ghee 1L Tin",
            hsn_code="040590",
            qty=100.0,
            unit_price=500.0,
            tax_rate=18.0,
            tax_amount=9000.0,
            total=59000.0,
        )
    ]
    invoice_repo.create_invoice(invoice, items=items)

    einvoice_service = EinvoiceService(
        invoice_repo=invoice_repo,
        business_repo=business_repo,
        audit_repo=audit_repo,
        provider=SandboxGspProvider(),
    )

    res = einvoice_service.generate_irn("inv-irn-test-1", current_user=test_user)

    assert len(res.irn) == 64
    # Hexadecimal format check
    int(res.irn, 16)
    assert len(res.ack_no) >= 15
    assert "SellerGstin" in res.qr_code
    assert "07AAAAA1234A1Z5" in res.qr_code
    assert "040590" in res.qr_code

    # Verify saved to invoice in repository
    updated = invoice_repo.get_by_id("inv-irn-test-1")
    assert updated.e_invoice_irn == res.irn
    assert updated.e_invoice_ack_no == res.ack_no
    assert updated.e_invoice_qr_code == res.qr_code

    # Verify idempotency
    res2 = einvoice_service.generate_irn("inv-irn-test-1", current_user=test_user)
    assert res2.irn == res.irn
    assert res2.status == "ALREADY_GENERATED"


def test_eway_bill_generation_and_validity_calculation(test_user: CurrentUser):
    """E-Way Bill generation produces 12-digit number and distance-based validity period."""
    invoice_repo = InMemoryInvoiceRepository()
    business_repo = InMemoryBusinessSettingsRepository()
    audit_repo = InMemoryAuditRepository()

    now = datetime.now(UTC)
    invoice = Invoice(
        id="inv-ewb-test-1",
        invoice_no="INV/2026-27/0056",
        invoice_date=now,
        gst_rate=18.0,
        subtotal=65000.0,
        tax_amount=11700.0,
        total_amount=76700.0,
        status=InvoiceStatusEnum.UNPAID,
        created_at=now,
    )
    invoice_repo.create_invoice(invoice, items=[])

    einvoice_service = EinvoiceService(
        invoice_repo=invoice_repo,
        business_repo=business_repo,
        audit_repo=audit_repo,
        provider=SandboxGspProvider(),
    )

    req = EWayBillGenerateRequest(
        vehicle_no="HR 26 DQ 1234",
        transporter_name="FastFreight Logistics",
        distance_km=350,
    )

    ewb_res = einvoice_service.generate_eway_bill("inv-ewb-test-1", req, current_user=test_user)

    assert len(ewb_res.e_way_bill_no) == 12
    assert ewb_res.vehicle_no == "HR26DQ1234"
    assert ewb_res.valid_until > ewb_res.e_way_bill_date

    # Verify updated in DB
    updated = invoice_repo.get_by_id("inv-ewb-test-1")
    assert updated.e_way_bill_no == ewb_res.e_way_bill_no


def test_einvoice_and_eway_bill_api_router_endpoints(test_user: CurrentUser):
    """Test HTTP API router endpoints for E-Invoice config, IRN generation, and E-Way Bill."""
    app = create_app()

    invoice_repo = InMemoryInvoiceRepository()
    business_repo = InMemoryBusinessSettingsRepository()
    audit_repo = InMemoryAuditRepository()

    now = datetime.now(UTC)
    invoice = Invoice(
        id="inv-http-1",
        invoice_no="INV/2026-27/0057",
        invoice_date=now,
        gst_rate=18.0,
        subtotal=10000.0,
        tax_amount=1800.0,
        total_amount=11800.0,
        status=InvoiceStatusEnum.UNPAID,
        created_at=now,
    )
    invoice_repo.create_invoice(invoice, items=[])

    test_einvoice_svc = EinvoiceService(
        invoice_repo=invoice_repo,
        business_repo=business_repo,
        audit_repo=audit_repo,
        provider=SandboxGspProvider(),
        settings=Settings(einvoice_enabled=False, gsp_provider="sandbox"),
    )

    from app.core.di import get_einvoice_service

    app.dependency_overrides[get_einvoice_service] = lambda: test_einvoice_svc
    app.dependency_overrides[get_current_user] = lambda: test_user
    app.dependency_overrides[require_permission("orders:manage")] = lambda: test_user

    client = TestClient(app)

    # 1. Config endpoint
    config_res = client.get("/invoices/einvoice/config")
    assert config_res.status_code == 200
    assert config_res.json()["is_sandbox"] is True
    assert "₹5 Crore" in config_res.json()["turnover_threshold_notice"]

    # 2. Generate IRN
    irn_res = client.post("/invoices/inv-http-1/generate-irn")
    assert irn_res.status_code == 200
    assert len(irn_res.json()["irn"]) == 64

    # 3. Generate E-Way Bill
    ewb_res = client.post(
        "/invoices/inv-http-1/generate-eway-bill",
        json={"vehicle_no": "DL01AB9876", "distance_km": 120},
    )
    assert ewb_res.status_code == 200
    assert len(ewb_res.json()["e_way_bill_no"]) == 12
