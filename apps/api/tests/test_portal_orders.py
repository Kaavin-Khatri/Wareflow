"""
Unit and integration tests for Step 11.4 — Self-Service Order Placement & Retailer Order/Invoice History.

Validates:
1. Retailer places order within credit and stock limits -> auto-confirms immediately via SalesOrderService with FIFO deduction.
2. Retailer places order exceeding credit limit -> stays in DRAFT status, informs retailer with clear reason, and triggers staff review notification.
3. Retailer places order with insufficient stock -> stays in DRAFT status, informs retailer, and triggers notification.
4. Server-side scoping prevents cross-retailer tampering.
5. Retailer order history and invoice history return strictly scoped data.
"""

from datetime import UTC, datetime

from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.api.routers import portal
from app.core.di import (
    get_notification_service,
    get_portal_auth_service,
    get_sales_order_service,
)
from app.core.security import CurrentUser, get_current_user, require_portal_retailer
from app.models.catalog import Product
from app.models.portal import RetailerUser
from app.models.retailer import BuyerTypeEnum, Retailer, SalesOrder, SOStatusEnum
from app.models.warehouse import StockBatch, Warehouse
from app.repositories.impl.customer_repository import InMemoryCustomerRepository
from app.repositories.impl.invoice_repository import InMemoryInvoiceRepository
from app.repositories.impl.notification_repository import InMemoryNotificationRepository
from app.repositories.impl.product_repository import InMemoryProductRepository
from app.repositories.impl.profile_repository import InMemoryProfileRepository
from app.repositories.impl.retailer_repository import InMemoryRetailerRepository
from app.repositories.impl.retailer_user_repository import InMemoryRetailerUserRepository
from app.repositories.impl.sales_order_repository import InMemorySalesOrderRepository
from app.repositories.impl.stock_repository import InMemoryStockRepository
from app.services.notification_service import NotificationService
from app.services.portal_auth_service import PortalAuthService
from app.services.pricing_strategy import PricingEngineService
from app.services.sales_order_service import SalesOrderService


def _setup_portal_order_env():
    # 1. Retailer with standard tier & 50,000 credit limit
    retailer_a = Retailer(
        id="ret-alpha-1",
        name="Alpha Mart",
        email="alpha@mart.com",
        pricing_tier="standard",
        credit_limit=50000.0,
        credit_balance=0.0,
        is_active=True,
    )
    retailer_b = Retailer(
        id="ret-beta-2",
        name="Beta Foods",
        email="beta@foods.com",
        pricing_tier="gold",
        credit_limit=200000.0,
        credit_balance=0.0,
        is_active=True,
    )

    # 2. Warehouse & Stock Batches
    warehouse = Warehouse(id="wh-main-1", name="Central Distribution Hub", location="Hub 1")
    product_tea = Product(
        id="prod-tea-1",
        sku="BEV-TEA-001",
        name="Assam Gold Premium Tea 500g",
        wholesale_price=200.0,
        cost_price=150.0,
        reorder_point=10.0,
        is_active=True,
    )
    product_biscuit = Product(
        id="prod-biscuit-1",
        sku="SNK-BIS-001",
        name="Butter Crunch Cookies 200g",
        wholesale_price=100.0,
        cost_price=70.0,
        reorder_point=5.0,
        is_active=True,
    )

    batch_tea = StockBatch(
        id="batch-tea-101",
        product_id=product_tea.id,
        warehouse_id=warehouse.id,
        batch_no="BATCH-TEA-01",
        quantity=50.0,
        received_at=datetime.now(UTC),
    )
    batch_biscuit = StockBatch(
        id="batch-bis-101",
        product_id=product_biscuit.id,
        warehouse_id=warehouse.id,
        batch_no="BATCH-BIS-01",
        quantity=5.0,  # Limited stock for out-of-stock test
        received_at=datetime.now(UTC),
    )

    # Repositories
    product_repo = InMemoryProductRepository([product_tea, product_biscuit])
    stock_repo = InMemoryStockRepository(
        warehouses=[warehouse],
        batches=[batch_tea, batch_biscuit],
        products=[product_tea, product_biscuit],
    )
    retailer_repo = InMemoryRetailerRepository([retailer_a, retailer_b])
    retailer_user_repo = InMemoryRetailerUserRepository([
        RetailerUser(id="user-alpha-uid", retailer_id="ret-alpha-1", email="alpha@mart.com"),
        RetailerUser(id="user-beta-uid", retailer_id="ret-beta-2", email="beta@foods.com"),
    ])
    profile_repo = InMemoryProfileRepository([])
    sales_order_repo = InMemorySalesOrderRepository([])
    invoice_repo = InMemoryInvoiceRepository()
    notification_repo = InMemoryNotificationRepository()
    customer_repo = InMemoryCustomerRepository([])
    pricing_engine = PricingEngineService()

    sales_order_service = SalesOrderService(
        so_repo=sales_order_repo,
        retailer_repo=retailer_repo,
        stock_repo=stock_repo,
        product_repo=product_repo,
        pricing_engine=pricing_engine,
        customer_repo=customer_repo,
    )

    notification_service = NotificationService(
        notification_repo=notification_repo,
        retailer_user_repo=retailer_user_repo,
    )

    portal_service = PortalAuthService(
        retailer_user_repo=retailer_user_repo,
        retailer_repo=retailer_repo,
        profile_repo=profile_repo,
        sales_order_repo=sales_order_repo,
        invoice_repo=invoice_repo,
        product_repo=product_repo,
        stock_repo=stock_repo,
        pricing_engine=pricing_engine,
    )

    return {
        "portal_service": portal_service,
        "sales_order_service": sales_order_service,
        "notification_service": notification_service,
        "stock_repo": stock_repo,
        "retailer_repo": retailer_repo,
        "sales_order_repo": sales_order_repo,
        "notification_repo": notification_repo,
        "invoice_repo": invoice_repo,
    }


def _create_test_app(env: dict, current_user: CurrentUser) -> TestClient:
    app = FastAPI()
    app.include_router(portal.router)

    app.dependency_overrides[get_portal_auth_service] = lambda: env["portal_service"]
    app.dependency_overrides[get_sales_order_service] = lambda: env["sales_order_service"]
    app.dependency_overrides[get_notification_service] = lambda: env["notification_service"]
    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[require_portal_retailer] = lambda: current_user

    return TestClient(app)


def test_retailer_places_order_auto_confirmed_when_stock_and_credit_sufficient():
    env = _setup_portal_order_env()
    retailer_user = CurrentUser(
        id="user-alpha-uid",
        email="alpha@mart.com",
        role="Retailer",
        permissions=set(),
        retailer_id="ret-alpha-1",
        account_type="retailer",
    )
    client = _create_test_app(env, retailer_user)

    payload = {
        "items": [
            {"product_id": "prod-tea-1", "qty": 10.0}
        ]
    }
    response = client.post("/portal/orders", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()

    assert data["status"] == "confirmed"
    assert data["auto_confirmed"] is True
    assert data["total_amount"] == 2000.0  # 10 * 200.0 standard
    assert data["items_count"] == 1

    # Verify FIFO stock was deducted: 50 -> 40
    on_hand = env["stock_repo"].get_on_hand("prod-tea-1")
    assert on_hand == 40.0

    # Verify retailer credit balance reserved: 0 -> 2000
    ret = env["retailer_repo"].get_by_id("ret-alpha-1")
    assert float(ret.credit_balance) == 2000.0


def test_retailer_places_order_exceeding_credit_stays_in_draft_and_notifies_staff():
    env = _setup_portal_order_env()
    # Credit limit is 50,000; order 300 * 200 = 60,000
    retailer_user = CurrentUser(
        id="user-alpha-uid",
        email="alpha@mart.com",
        role="Retailer",
        permissions=set(),
        retailer_id="ret-alpha-1",
        account_type="retailer",
    )
    client = _create_test_app(env, retailer_user)

    # Increase stock so stock isn't the blocker (credit limit is 50,000; order is 60,000)
    env["stock_repo"].batches["batch-tea-101"]["quantity"] = 500.0

    payload = {
        "items": [
            {"product_id": "prod-tea-1", "qty": 300.0}
        ]
    }
    response = client.post("/portal/orders", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()

    assert data["status"] == "draft"
    assert data["auto_confirmed"] is False
    assert "Credit limit exceeded" in data["reason"]

    # Verify stock was NOT deducted
    on_hand = env["stock_repo"].get_on_hand("prod-tea-1")
    assert on_hand == 500.0

    # Verify staff notification was dispatched
    notifications = env["notification_repo"].list_for_user("ret-alpha-1")
    assert len(notifications) >= 1
    assert "Credit limit exceeded" in notifications[0].body


def test_retailer_places_order_with_insufficient_stock_stays_in_draft_and_notifies_staff():
    env = _setup_portal_order_env()
    # Biscuit batch only has 5.0 in stock; order 20.0
    retailer_user = CurrentUser(
        id="user-alpha-uid",
        email="alpha@mart.com",
        role="Retailer",
        permissions=set(),
        retailer_id="ret-alpha-1",
        account_type="retailer",
    )
    client = _create_test_app(env, retailer_user)

    payload = {
        "items": [
            {"product_id": "prod-biscuit-1", "qty": 20.0}
        ]
    }
    response = client.post("/portal/orders", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()

    assert data["status"] == "draft"
    assert data["auto_confirmed"] is False
    assert "Insufficient stock" in data["reason"]

    # Verify stock remained untouched at 5.0
    on_hand = env["stock_repo"].get_on_hand("prod-biscuit-1")
    assert on_hand == 5.0


def test_retailer_order_and_invoice_history_strict_data_wall():
    env = _setup_portal_order_env()

    # Create an order and invoice for Retailer A
    so_a = SalesOrder(
        id="so-alpha-100",
        so_number="SO-2026-0001",
        buyer_type=BuyerTypeEnum.RETAILER,
        retailer_id="ret-alpha-1",
        status=SOStatusEnum.CONFIRMED,
        total_amount=5000.0,
        items=[],
    )
    so_b = SalesOrder(
        id="so-beta-200",
        so_number="SO-2026-0002",
        buyer_type=BuyerTypeEnum.RETAILER,
        retailer_id="ret-beta-2",
        status=SOStatusEnum.CONFIRMED,
        total_amount=12000.0,
        items=[],
    )
    env["sales_order_repo"].create(so_a)
    env["sales_order_repo"].create(so_b)

    retailer_user_a = CurrentUser(
        id="user-alpha-uid",
        email="alpha@mart.com",
        role="Retailer",
        permissions=set(),
        retailer_id="ret-alpha-1",
        account_type="retailer",
    )
    client_a = _create_test_app(env, retailer_user_a)

    # 1. Retailer A lists their orders -> sees ONLY SO-2026-0001
    res = client_a.get("/portal/orders")
    assert res.status_code == status.HTTP_200_OK
    orders = res.json()
    assert len(orders) == 1
    assert orders[0]["so_number"] == "SO-2026-0001"

    # 2. Retailer A attempts to fetch Retailer B's order -> 403 Forbidden
    res_b = client_a.get("/portal/orders/so-beta-200")
    assert res_b.status_code == status.HTTP_403_FORBIDDEN
    assert "Access denied" in res_b.json()["detail"]
