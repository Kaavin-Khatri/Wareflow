"""Tests for Packing Slip and Pick List PDF generation (Phase 12 Step 12.2)."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.core.di import get_export_service
from app.core.security import CurrentUser, get_current_user
from app.main import app
from app.models.delivery import Delivery, DeliveryStatusEnum
from app.models.retailer import BuyerTypeEnum, Retailer, SalesOrder, SalesOrderItem, SOStatusEnum
from app.repositories.impl.business_settings_repository import InMemoryBusinessSettingsRepository
from app.repositories.impl.delivery_repository import InMemoryDeliveryRepository
from app.repositories.impl.sales_order_repository import InMemorySalesOrderRepository
from app.schemas.business_settings import BusinessSettingsResponse
from app.services.export_service import ExportService


class MockWarehouseProduct:
    def __init__(self, sku: str, name: str, unit: str = "PCS", warehouse_name: str | None = None):
        self.sku = sku
        self.name = name
        self.unit = unit
        self.base_uom = None
        self.storage_location = "Aisle 4, Bay B"
        if warehouse_name:
            self.warehouse = type("WH", (), {"name": warehouse_name})()
        else:
            self.warehouse = None


def test_pick_list_generation_has_checkboxes_quantities_and_zero_prices():
    """Pick list must show large checklist format, warehouse location, and strictly ZERO pricing info."""
    so_repo = InMemorySalesOrderRepository()
    settings_repo = InMemoryBusinessSettingsRepository()
    delivery_repo = InMemoryDeliveryRepository()
    export_service = ExportService(
        sales_order_repo=so_repo,
        business_settings_repo=settings_repo,
        delivery_repo=delivery_repo,
    )

    retailer = Retailer(
        id="ret-pick-1",
        name="Apex Wholesale Mart",
        contact_person="Sunil Varma",
        phone="+91 98200 11223",
        address="Gala 14, APMC Market, Vashi, Navi Mumbai",
    )

    order = SalesOrder(
        id="so-pick-1",
        so_number="SO-2026-PICK-01",
        retailer_id=retailer.id,
        buyer_type=BuyerTypeEnum.RETAILER,
        status=SOStatusEnum.CONFIRMED,
        order_date=datetime.now(UTC),
        total_amount=15450.75,  # Real monetary total in database
    )
    order.retailer = retailer

    prod1 = MockWarehouseProduct(sku="WHEAT-10KG", name="Premium Sharbati Wheat Flour 10kg", unit="BAG")
    prod2 = MockWarehouseProduct(sku="RICE-BAS-5KG", name="Royal Basmati Rice 5kg", unit="BAG")

    item1 = SalesOrderItem(
        id="item-1",
        so_id=order.id,
        product_id="prod-1",
        qty=12.0,
        unit_price=450.00,  # Prices present in line items
    )
    item1.product = prod1  # type: ignore

    item2 = SalesOrderItem(
        id="item-2",
        so_id=order.id,
        product_id="prod-2",
        qty=8.0,
        unit_price=1250.00,
    )
    item2.product = prod2  # type: ignore

    order.items = [item1, item2]
    so_repo.orders[order.id] = order

    # Generate Pick List PDF bytes
    pdf_bytes = export_service.generate_pick_list(order.id)

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF-")

    # Verify text representation in PDF does not contain currency symbols or prices
    pdf_text = pdf_bytes.decode("latin1", errors="ignore")

    # Document identifiers and structure present
    assert "WAREHOUSE PICK LIST" in pdf_text or "Pick" in pdf_text
    assert "SO-2026-PICK-01" in pdf_text
    assert "Apex Wholesale Mart" in pdf_text
    assert "WHEAT-10KG" in pdf_text
    assert "RICE-BAS-5KG" in pdf_text

    # STRICT ZERO-PRICE GUARDRAIL: Verify no price amounts or currency symbols in PDF content
    assert "15450.75" not in pdf_text
    assert "450.00" not in pdf_text
    assert "1250.00" not in pdf_text
    assert "₹" not in pdf_text
    assert "INR" not in pdf_text
    assert "Unit Price" not in pdf_text
    assert "Total Amount" not in pdf_text


def test_pick_list_groups_by_multiple_warehouses():
    """Multi-warehouse order items must be grouped by warehouse on the pick list."""
    so_repo = InMemorySalesOrderRepository()
    export_service = ExportService(sales_order_repo=so_repo)

    order = SalesOrder(
        id="so-multi-wh-1",
        so_number="SO-2026-MULTI-01",
        buyer_type=BuyerTypeEnum.CUSTOMER,
        status=SOStatusEnum.PACKED,
        order_date=datetime.now(UTC),
        total_amount=5000.0,
    )

    prod_central = MockWarehouseProduct(sku="OIL-1L", name="Refined Sunflower Oil 1L", warehouse_name="Central Depot")
    prod_cold = MockWarehouseProduct(sku="BUTTER-500G", name="Pasteurized Butter 500g", warehouse_name="Cold Storage Facility")

    item1 = SalesOrderItem(id="it-1", so_id=order.id, product_id="p1", qty=20.0, unit_price=150.0)
    item1.product = prod_central  # type: ignore

    item2 = SalesOrderItem(id="it-2", so_id=order.id, product_id="p2", qty=15.0, unit_price=200.0)
    item2.product = prod_cold  # type: ignore

    order.items = [item1, item2]
    so_repo.orders[order.id] = order

    pdf_bytes = export_service.generate_pick_list(order.id)
    pdf_text = pdf_bytes.decode("latin1", errors="ignore")

    assert "Central Depot" in pdf_text
    assert "Cold Storage Facility" in pdf_text
    assert "OIL-1L" in pdf_text
    assert "BUTTER-500G" in pdf_text


def test_packing_slip_generation_is_print_ready_and_zero_prices():
    """Packing slip must be customer-facing, print-ready on A4, and contain strictly ZERO prices."""
    so_repo = InMemorySalesOrderRepository()
    settings_repo = InMemoryBusinessSettingsRepository()
    delivery_repo = InMemoryDeliveryRepository()

    settings_repo._settings = BusinessSettingsResponse(
        id="bs-1",
        business_name="Shree Ganesh Traders",
        legal_name="SHREE GANESH WHOLESALE DISTRIBUTORS",
        gstin="27AABCS1429B1ZB",
        fssai_license_no="11521001000456",
        phone="+91 22 2500 4455",
        email="orders@shreeganesh.in",
        address="Plot 55, MIDC Industrial Area, Kurla West, Mumbai 400070",
    )

    export_service = ExportService(
        sales_order_repo=so_repo,
        business_settings_repo=settings_repo,
        delivery_repo=delivery_repo,
    )

    retailer = Retailer(
        id="ret-pack-1",
        name="Kiran Supermarket",
        contact_person="Kiran Patel",
        phone="+91 99887 66554",
        address="Shop 1-3, Royal Palm Heights, Borivali East, Mumbai 400066",
    )

    order = SalesOrder(
        id="so-pack-1",
        so_number="SO-2026-PACK-01",
        retailer_id=retailer.id,
        buyer_type=BuyerTypeEnum.RETAILER,
        status=SOStatusEnum.SHIPPED,
        order_date=datetime.now(UTC),
        total_amount=28900.50,
    )
    order.retailer = retailer

    prod1 = MockWarehouseProduct(sku="DAL-TUR-1KG", name="Toor Dal Desi Polished 1kg", unit="PKT")
    prod2 = MockWarehouseProduct(sku="SUGAR-M30-5KG", name="Refined Crystal Sugar M-30 5kg", unit="BAG")

    item1 = SalesOrderItem(id="it-1", so_id=order.id, product_id="p1", qty=25.0, unit_price=180.00)
    item1.product = prod1  # type: ignore

    item2 = SalesOrderItem(id="it-2", so_id=order.id, product_id="p2", qty=10.0, unit_price=220.00)
    item2.product = prod2  # type: ignore

    order.items = [item1, item2]
    so_repo.orders[order.id] = order

    # Assign a delivery
    delivery = Delivery(
        id="del-pack-1",
        sales_order_id=order.id,
        driver_name="Mahesh Yadav",
        vehicle_no="MH-03-CB-9080",
        status=DeliveryStatusEnum.OUT_FOR_DELIVERY,
    )
    delivery_repo._deliveries[delivery.id] = delivery

    pdf_bytes = export_service.generate_packing_slip(order.id)

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF-")

    pdf_text = pdf_bytes.decode("latin1", errors="ignore")

    # Distributor header & document elements
    assert "Shree Ganesh Traders" in pdf_text
    assert "27AABCS1429B1ZB" in pdf_text
    assert "11521001000456" in pdf_text
    assert "PACKING SLIP" in pdf_text
    assert "SO-2026-PACK-01" in pdf_text
    assert "Kiran Supermarket" in pdf_text
    assert "Mahesh Yadav" in pdf_text
    assert "MH-03-CB-9080" in pdf_text
    assert "DAL-TUR-1KG" in pdf_text
    assert "SUGAR-M30-5KG" in pdf_text

    # ZERO PRICING GUARD: No invoice amounts or rupee symbols
    assert "28900.50" not in pdf_text
    assert "180.00" not in pdf_text
    assert "220.00" not in pdf_text
    assert "₹" not in pdf_text
    assert "Invoice Total" not in pdf_text


def test_http_pdf_endpoints_integration():
    """FastAPI endpoints for packing slip and pick list return streaming PDF responses with 200 OK."""
    test_user = CurrentUser(
        id="user-dispatch-1",
        email="dispatch@wareflow.io",
        role="Manager",
        permissions=["orders:view", "inventory:manage"],
    )

    so_repo = InMemorySalesOrderRepository()
    settings_repo = InMemoryBusinessSettingsRepository()
    export_service = ExportService(
        sales_order_repo=so_repo,
        business_settings_repo=settings_repo,
    )

    order = SalesOrder(
        id="so-http-pdf-1",
        so_number="SO-2026-HTTP-01",
        buyer_type=BuyerTypeEnum.CUSTOMER,
        status=SOStatusEnum.CONFIRMED,
        order_date=datetime.now(UTC),
        total_amount=1200.0,
    )
    prod = MockWarehouseProduct(sku="SOAP-BOX-10", name="Bath Soap 10-Pack", unit="BOX")
    item = SalesOrderItem(id="it-1", so_id=order.id, product_id="p1", qty=5.0, unit_price=240.0)
    item.product = prod  # type: ignore
    order.items = [item]
    so_repo.orders[order.id] = order

    app.dependency_overrides[get_current_user] = lambda: test_user
    app.dependency_overrides[get_export_service] = lambda: export_service

    client = TestClient(app)

    try:
        # 1. Packing slip
        resp_pack = client.get("/sales-orders/so-http-pdf-1/packing-slip.pdf")
        assert resp_pack.status_code == 200
        assert resp_pack.headers["content-type"] == "application/pdf"
        assert 'filename="packing-slip-so-http-pdf-1.pdf"' in resp_pack.headers["content-disposition"]
        assert resp_pack.content.startswith(b"%PDF-")

        # 2. Pick list
        resp_pick = client.get("/sales-orders/so-http-pdf-1/pick-list.pdf")
        assert resp_pick.status_code == 200
        assert resp_pick.headers["content-type"] == "application/pdf"
        assert 'filename="pick-list-so-http-pdf-1.pdf"' in resp_pick.headers["content-disposition"]
        assert resp_pick.content.startswith(b"%PDF-")

        # 3. 404 for non-existent order
        resp_404 = client.get("/sales-orders/non-existent-order/pick-list.pdf")
        assert resp_404.status_code == 404

    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_export_service, None)
