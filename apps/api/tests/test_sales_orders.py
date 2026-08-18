"""Automated test suite for Sales Orders, FIFO stock deduction, credit gate, and fulfillment."""

from datetime import UTC, date, datetime, timedelta

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.routers.sales_orders import router as sales_orders_router
from app.core.di import get_sales_order_service
from app.core.security import CurrentUser, get_current_user, require_permission
from app.models.catalog import Product
from app.models.inventory import StockMovementTypeEnum
from app.models.retailer import BuyerTypeEnum, Retailer, SOStatusEnum
from app.repositories.impl.product_repository import InMemoryProductRepository
from app.repositories.impl.retailer_repository import InMemoryRetailerRepository
from app.repositories.impl.sales_order_repository import InMemorySalesOrderRepository
from app.repositories.impl.stock_repository import InMemoryStockRepository
from app.schemas.sales_orders import (
    SalesOrderCreateRequest,
    SalesOrderItemCreateRequest,
    SalesOrderStatusUpdateRequest,
)
from app.services.pricing_strategy import PricingEngineService, StandardPricingStrategy
from app.services.sales_order_service import SalesOrderService


@pytest.fixture
def dummy_admin_user() -> CurrentUser:
    """Fixture providing an authenticated admin user."""
    return CurrentUser(
        id="usr-admin-1",
        email="admin@wareflow.io",
        display_name="Operations Admin",
        role="Manager",
        permissions={"inventory:view", "inventory:manage", "orders:create", "orders:view"},
    )


@pytest.fixture
def sales_order_setup():
    """Setup in-memory repositories and service for isolated sales order tests."""
    prod_id = "prod-rice-1"
    wh_id = "wh-main-1"
    ret_id = "ret-apex-1"

    warehouses = [
        {"id": wh_id, "name": "Central Pune Warehouse", "location": "Pune", "is_active": True}
    ]
    products = [
        {
            "id": prod_id,
            "sku": "RIC-BAS-001",
            "name": "Royal Basmati Rice 5kg",
            "cost_price": 400.0,
            "wholesale_price": 500.0,
            "reorder_point": 10.0,
            "reorder_qty": 50.0,
            "is_active": True,
        }
    ]
    batches = [
        {
            "id": "batch-1",
            "product_id": prod_id,
            "warehouse_id": wh_id,
            "batch_no": "B-2026-001",
            "quantity": 10.0,
            "expiry_date": date.today() + timedelta(days=30),  # Oldest expiry (FIFO 1st)
            "received_at": datetime.now(UTC) - timedelta(days=20),
        },
        {
            "id": "batch-2",
            "product_id": prod_id,
            "warehouse_id": wh_id,
            "batch_no": "B-2026-002",
            "quantity": 15.0,
            "expiry_date": date.today() + timedelta(days=90),  # Newer expiry (FIFO 2nd)
            "received_at": datetime.now(UTC) - timedelta(days=10),
        },
    ]

    retailers = [
        Retailer(
            id=ret_id,
            name="Apex Kirana Stores",
            contact_person="Ramesh Patel",
            phone="9876543210",
            email="ramesh@apex.in",
            pricing_tier="standard",
            credit_limit=20000.0,
            credit_balance=5000.0,
            is_active=True,
        )
    ]

    stock_repo = InMemoryStockRepository(warehouses=warehouses, products=products, batches=batches)
    product_repo = InMemoryProductRepository(seed_products=[Product(**products[0])])
    retailer_repo = InMemoryRetailerRepository(initial_data=retailers)

    so_repo = InMemorySalesOrderRepository()

    pricing_engine = PricingEngineService()
    pricing_engine.register_strategy(StandardPricingStrategy())

    service = SalesOrderService(
        so_repo=so_repo,
        retailer_repo=retailer_repo,
        stock_repo=stock_repo,
        product_repo=product_repo,
        pricing_engine=pricing_engine,
    )

    return {
        "service": service,
        "stock_repo": stock_repo,
        "retailer_repo": retailer_repo,
        "so_repo": so_repo,
        "prod_id": prod_id,
        "ret_id": ret_id,
    }


def test_confirm_order_fifo_stock_deduction_and_credit(sales_order_setup, dummy_admin_user):
    """QA 1: Confirming order with sufficient stock AND credit deducts batches oldest-first."""
    s = sales_order_setup
    service: SalesOrderService = s["service"]
    stock_repo: InMemoryStockRepository = s["stock_repo"]
    retailer_repo: InMemoryRetailerRepository = s["retailer_repo"]

    # 1. Create order for 18 units @ 500 = ₹9,000
    create_req = SalesOrderCreateRequest(
        buyer_type=BuyerTypeEnum.RETAILER,
        retailer_id=s["ret_id"],
        items=[SalesOrderItemCreateRequest(product_id=s["prod_id"], qty=18.0)],
    )
    created = service.create_order(create_req, current_user=dummy_admin_user)
    assert created.status == SOStatusEnum.DRAFT
    assert created.total_amount == 9000.0

    # 2. Confirm order
    confirmed = service.confirm_order(created.id, current_user=dummy_admin_user)
    assert confirmed.status == SOStatusEnum.CONFIRMED

    # 3. Verify FIFO Batch Deductions:
    # Batch 1 had 10 -> should be 0.0
    # Batch 2 had 15 -> should be 15 - 8 = 7.0
    b1 = stock_repo.get_batch_by_id("batch-1")
    b2 = stock_repo.get_batch_by_id("batch-2")
    assert b1.quantity == 0.0
    assert b2.quantity == 7.0

    # 4. Verify Stock Movements (2 OUT movements)
    out_movements = [m for m in stock_repo.movements if m["type"] == StockMovementTypeEnum.OUT]
    assert len(out_movements) == 2
    assert out_movements[0]["batch_id"] == "batch-1"
    assert out_movements[0]["quantity"] == 10.0
    assert out_movements[1]["batch_id"] == "batch-2"
    assert out_movements[1]["quantity"] == 8.0

    # 5. Verify Credit Balance updated: 5,000 + 9,000 = 14,000
    ret = retailer_repo.get_by_id(s["ret_id"])
    assert ret.credit_balance == 14000.0


def test_confirm_order_credit_limit_exceeded_blocks_and_deducts_zero_stock(
    sales_order_setup, dummy_admin_user
):
    """QA 2: Confirming order that exceeds credit limit is blocked with shortfall named, deducting ZERO stock."""
    s = sales_order_setup
    service: SalesOrderService = s["service"]
    stock_repo: InMemoryStockRepository = s["stock_repo"]
    retailer_repo: InMemoryRetailerRepository = s["retailer_repo"]

    # Retailer credit limit: 20,000, current balance: 5,000. Available credit: 15,000.
    # Create order for 35 units @ 500 = ₹17,500. Proposed balance: 22,500. Shortfall: ₹2,500.
    create_req = SalesOrderCreateRequest(
        buyer_type=BuyerTypeEnum.RETAILER,
        retailer_id=s["ret_id"],
        items=[SalesOrderItemCreateRequest(product_id=s["prod_id"], qty=35.0)],
    )
    created = service.create_order(create_req, current_user=dummy_admin_user)

    with pytest.raises(HTTPException) as exc_info:
        service.confirm_order(created.id, current_user=dummy_admin_user)

    assert exc_info.value.status_code == 422
    assert "Credit limit exceeded" in exc_info.value.detail
    assert "shortfall ₹2500.00" in exc_info.value.detail

    # Verify ZERO stock was touched
    b1 = stock_repo.get_batch_by_id("batch-1")
    b2 = stock_repo.get_batch_by_id("batch-2")
    assert b1.quantity == 10.0
    assert b2.quantity == 15.0
    assert len(stock_repo.movements) == 0

    # Verify credit balance untouched
    ret = retailer_repo.get_by_id(s["ret_id"])
    assert ret.credit_balance == 5000.0


def test_confirm_order_cash_only_zero_credit_limit_allowed(sales_order_setup, dummy_admin_user):
    """Zero credit limit represents cash-only accounts and is never credit-blocked."""
    s = sales_order_setup
    service: SalesOrderService = s["service"]
    retailer_repo: InMemoryRetailerRepository = s["retailer_repo"]

    # Set credit limit to 0
    retailer_repo.update(s["ret_id"], {"credit_limit": 0.0, "credit_balance": 0.0})

    create_req = SalesOrderCreateRequest(
        buyer_type=BuyerTypeEnum.RETAILER,
        retailer_id=s["ret_id"],
        items=[SalesOrderItemCreateRequest(product_id=s["prod_id"], qty=5.0)],
    )
    created = service.create_order(create_req, current_user=dummy_admin_user)
    confirmed = service.confirm_order(created.id, current_user=dummy_admin_user)
    assert confirmed.status == SOStatusEnum.CONFIRMED


def test_confirm_order_insufficient_stock_blocks_confirmation(sales_order_setup, dummy_admin_user):
    """QA 3: Confirming order that exceeds on-hand stock is blocked with exact shortfall named."""
    s = sales_order_setup
    service: SalesOrderService = s["service"]
    retailer_repo: InMemoryRetailerRepository = s["retailer_repo"]

    # Increase credit limit so credit passes
    retailer_repo.update(s["ret_id"], {"credit_limit": 100000.0})

    # Available stock = 10 + 15 = 25. Order 30 units (shortfall = 5).
    create_req = SalesOrderCreateRequest(
        buyer_type=BuyerTypeEnum.RETAILER,
        retailer_id=s["ret_id"],
        items=[SalesOrderItemCreateRequest(product_id=s["prod_id"], qty=30.0)],
    )
    created = service.create_order(create_req, current_user=dummy_admin_user)

    with pytest.raises(HTTPException) as exc_info:
        service.confirm_order(created.id, current_user=dummy_admin_user)

    assert exc_info.value.status_code == 422
    assert "Insufficient stock for product" in exc_info.value.detail
    assert "shortfall 5.0" in exc_info.value.detail

    # Verify credit balance was not incremented
    ret = retailer_repo.get_by_id(s["ret_id"])
    assert ret.credit_balance == 5000.0


def test_cancel_confirmed_order_restores_stock_via_compensating_movement(
    sales_order_setup, dummy_admin_user
):
    """QA 4: Cancelling a confirmed order restores stock via compensating adjustment movement."""
    s = sales_order_setup
    service: SalesOrderService = s["service"]
    stock_repo: InMemoryStockRepository = s["stock_repo"]
    retailer_repo: InMemoryRetailerRepository = s["retailer_repo"]

    # 1. Create and confirm order for 12 units (10 from b1, 2 from b2)
    create_req = SalesOrderCreateRequest(
        buyer_type=BuyerTypeEnum.RETAILER,
        retailer_id=s["ret_id"],
        items=[SalesOrderItemCreateRequest(product_id=s["prod_id"], qty=12.0)],
    )
    created = service.create_order(create_req, current_user=dummy_admin_user)
    service.confirm_order(created.id, current_user=dummy_admin_user)

    assert stock_repo.get_batch_by_id("batch-1").quantity == 0.0
    assert stock_repo.get_batch_by_id("batch-2").quantity == 13.0
    assert retailer_repo.get_by_id(s["ret_id"]).credit_balance == 11000.0

    # 2. Cancel the confirmed order
    cancelled = service.update_status(
        created.id,
        SalesOrderStatusUpdateRequest(status=SOStatusEnum.CANCELLED, notes="Customer changed mind"),
        current_user=dummy_admin_user,
    )
    assert cancelled.status == SOStatusEnum.CANCELLED

    # 3. Verify stock restored to original quantities
    assert stock_repo.get_batch_by_id("batch-1").quantity == 10.0
    assert stock_repo.get_batch_by_id("batch-2").quantity == 15.0

    # 4. Verify compensating ADJUSTMENT movements created
    adj_movements = [
        m for m in stock_repo.movements if m["type"] == StockMovementTypeEnum.ADJUSTMENT
    ]
    assert len(adj_movements) == 2
    assert adj_movements[0]["quantity"] == 10.0
    assert adj_movements[1]["quantity"] == 2.0

    # 5. Verify credit balance refunded back to initial 5,000
    assert retailer_repo.get_by_id(s["ret_id"]).credit_balance == 5000.0


def test_invalid_status_transitions_rejected(sales_order_setup, dummy_admin_user):
    """QA 5: Illegal status transitions are rejected."""
    s = sales_order_setup
    service: SalesOrderService = s["service"]

    create_req = SalesOrderCreateRequest(
        buyer_type=BuyerTypeEnum.RETAILER,
        retailer_id=s["ret_id"],
        items=[SalesOrderItemCreateRequest(product_id=s["prod_id"], qty=2.0)],
    )
    created = service.create_order(create_req, current_user=dummy_admin_user)

    # 1. Draft -> Shipped (Illegal)
    with pytest.raises(HTTPException) as exc_info:
        service.update_status(
            created.id,
            SalesOrderStatusUpdateRequest(status=SOStatusEnum.SHIPPED),
            current_user=dummy_admin_user,
        )
    assert exc_info.value.status_code == 422

    # 2. Draft -> Delivered (Illegal)
    with pytest.raises(HTTPException) as exc_info:
        service.update_status(
            created.id,
            SalesOrderStatusUpdateRequest(status=SOStatusEnum.DELIVERED),
            current_user=dummy_admin_user,
        )
    assert exc_info.value.status_code == 422

    # Advance to confirmed -> packed -> shipped -> delivered
    service.confirm_order(created.id, current_user=dummy_admin_user)
    service.update_status(
        created.id,
        SalesOrderStatusUpdateRequest(status=SOStatusEnum.PACKED),
        current_user=dummy_admin_user,
    )
    service.update_status(
        created.id,
        SalesOrderStatusUpdateRequest(status=SOStatusEnum.SHIPPED),
        current_user=dummy_admin_user,
    )
    service.update_status(
        created.id,
        SalesOrderStatusUpdateRequest(status=SOStatusEnum.DELIVERED),
        current_user=dummy_admin_user,
    )

    # 3. Delivered -> Cancelled (Illegal)
    with pytest.raises(HTTPException) as exc_info:
        service.update_status(
            created.id,
            SalesOrderStatusUpdateRequest(status=SOStatusEnum.CANCELLED),
            current_user=dummy_admin_user,
        )
    assert exc_info.value.status_code == 422


def test_sales_orders_api_router_lifecycle(sales_order_setup, dummy_admin_user):
    """Full HTTP API lifecycle test for sales orders."""
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(sales_orders_router)

    app.dependency_overrides[get_sales_order_service] = lambda: sales_order_setup["service"]
    app.dependency_overrides[get_current_user] = lambda: dummy_admin_user
    app.dependency_overrides[require_permission("inventory:manage")] = lambda: dummy_admin_user

    client = TestClient(app)

    # 1. Create order via POST /sales-orders
    payload = {
        "buyer_type": "retailer",
        "retailer_id": sales_order_setup["ret_id"],
        "items": [{"product_id": sales_order_setup["prod_id"], "qty": 4.0}],
    }
    create_resp = client.post("/sales-orders", json=payload)
    assert create_resp.status_code == 201
    order_data = create_resp.json()
    order_id = order_data["id"]
    assert order_data["status"] == "draft"
    assert order_data["total_amount"] == 2000.0

    # 2. Get order via GET /sales-orders/{id}
    get_resp = client.get(f"/sales-orders/{order_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == order_id

    # 3. Confirm order via POST /sales-orders/{id}/confirm
    confirm_resp = client.post(f"/sales-orders/{order_id}/confirm")
    assert confirm_resp.status_code == 200
    assert confirm_resp.json()["status"] == "confirmed"

    # 4. Advance status to packed via PATCH /sales-orders/{id}/status
    pack_resp = client.patch(f"/sales-orders/{order_id}/status", json={"status": "packed"})
    assert pack_resp.status_code == 200
    assert pack_resp.json()["status"] == "packed"

    # 5. List orders via GET /sales-orders
    list_resp = client.get("/sales-orders")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1
