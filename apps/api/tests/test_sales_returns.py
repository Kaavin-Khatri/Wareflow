"""Automated test suite for Retailer Sales Returns (RMA In) and condition-based restocking."""

from datetime import UTC, date, datetime, timedelta

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.di import get_sales_return_service
from app.core.security import CurrentUser, get_current_user
from app.main import app
from app.models.catalog import Product
from app.models.inventory import StockMovementTypeEnum
from app.models.retailer import BuyerTypeEnum, Retailer, SalesOrder, SalesOrderItem, SOStatusEnum
from app.models.returns import ReturnItemConditionEnum, SalesReturnStatusEnum
from app.repositories.impl.product_repository import InMemoryProductRepository
from app.repositories.impl.retailer_repository import InMemoryRetailerRepository
from app.repositories.impl.sales_order_repository import InMemorySalesOrderRepository
from app.repositories.impl.sales_return_repository import InMemorySalesReturnRepository
from app.repositories.impl.stock_repository import InMemoryStockRepository
from app.schemas.sales_returns import SalesReturnCreateRequest, SalesReturnItemCreateRequest
from app.services.sales_return_service import SalesReturnService


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
def sales_return_setup():
    """Setup isolated in-memory repositories and service for RMA In return testing."""
    prod_id = "prod-rice-1"
    wh_id = "wh-main-1"
    ret_id = "ret-apex-1"
    so_id = "so-2026-001"
    batch_id = "batch-1"

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
            "id": batch_id,
            "product_id": prod_id,
            "warehouse_id": wh_id,
            "batch_no": "B-2026-001",
            "quantity": 30.0,
            "expiry_date": date.today() + timedelta(days=60),
            "received_at": datetime.now(UTC) - timedelta(days=10),
        }
    ]
    retailers = [
        Retailer(
            id=ret_id,
            name="Apex Kirana Stores",
            contact_person="Ramesh Patel",
            phone="9876543210",
            email="ramesh@apex.in",
            pricing_tier="gold",
            credit_limit=50000.0,
            credit_balance=10000.0,
            is_active=True,
        )
    ]
    sales_orders = [
        SalesOrder(
            id=so_id,
            so_number="SO-202608-0001",
            buyer_type=BuyerTypeEnum.RETAILER,
            retailer_id=ret_id,
            status=SOStatusEnum.DELIVERED,
            order_date=datetime.now(UTC) - timedelta(days=2),
            total_amount=9000.0,
            items=[
                SalesOrderItem(
                    id="so-item-1",
                    so_id=so_id,
                    product_id=prod_id,
                    qty=20.0,
                    unit_price=450.0,
                )
            ],
        )
    ]

    stock_repo = InMemoryStockRepository(warehouses=warehouses, products=products, batches=batches)
    product_repo = InMemoryProductRepository(seed_products=[Product(**products[0])])
    retailer_repo = InMemoryRetailerRepository(initial_data=retailers)
    so_repo = InMemorySalesOrderRepository(initial_data=sales_orders)
    return_repo = InMemorySalesReturnRepository()

    service = SalesReturnService(
        return_repo=return_repo,
        sales_order_repo=so_repo,
        stock_repo=stock_repo,
        product_repo=product_repo,
    )

    return {
        "service": service,
        "stock_repo": stock_repo,
        "product_repo": product_repo,
        "retailer_repo": retailer_repo,
        "so_repo": so_repo,
        "return_repo": return_repo,
        "prod_id": prod_id,
        "wh_id": wh_id,
        "ret_id": ret_id,
        "so_id": so_id,
        "batch_id": batch_id,
    }


def test_create_sales_return_success(sales_return_setup, dummy_admin_user):
    """Test creating a valid return request for a delivered sales order."""
    service: SalesReturnService = sales_return_setup["service"]
    so_id = sales_return_setup["so_id"]
    prod_id = sales_return_setup["prod_id"]

    payload = SalesReturnCreateRequest(
        sales_order_id=so_id,
        reason="Wrong pack size ordered by retailer",
        items=[
            SalesReturnItemCreateRequest(
                product_id=prod_id,
                qty=5.0,
                condition=ReturnItemConditionEnum.RESELLABLE,
                reason="Unopened case",
            )
        ],
    )

    resp = service.create_return(payload=payload, current_user=dummy_admin_user)
    assert resp.id is not None
    assert resp.status == SalesReturnStatusEnum.REQUESTED
    assert resp.so_number == "SO-202608-0001"
    assert resp.retailer_id == sales_return_setup["ret_id"]
    assert len(resp.items) == 1
    assert resp.items[0].qty == 5.0
    assert resp.items[0].condition == ReturnItemConditionEnum.RESELLABLE
    # Unit price is ₹450 from SO item, 5 * 450 = ₹2250 credit adjustment
    assert resp.credit_adjustment_amount == 2250.0


def test_create_sales_return_blocks_exceeding_sold_quantity(sales_return_setup, dummy_admin_user):
    """QA: Verify that returning more than was originally sold on that order is blocked."""
    service: SalesReturnService = sales_return_setup["service"]
    so_id = sales_return_setup["so_id"]
    prod_id = sales_return_setup["prod_id"]

    # SO has 20 units sold. Requesting 25 units must fail.
    payload = SalesReturnCreateRequest(
        sales_order_id=so_id,
        reason="Excess return attempt",
        items=[
            SalesReturnItemCreateRequest(
                product_id=prod_id,
                qty=25.0,
                condition=ReturnItemConditionEnum.RESELLABLE,
            )
        ],
    )

    with pytest.raises(HTTPException) as exc_info:
        service.create_return(payload=payload, current_user=dummy_admin_user)

    assert exc_info.value.status_code == 422
    assert "maximum returnable quantity" in exc_info.value.detail.lower()
    assert "sold 20.0" in exc_info.value.detail.lower()


def test_create_sales_return_accounts_for_previous_returns(sales_return_setup, dummy_admin_user):
    """QA: Verify cumulative return checks across multiple return requests on the same SO."""
    service: SalesReturnService = sales_return_setup["service"]
    so_id = sales_return_setup["so_id"]
    prod_id = sales_return_setup["prod_id"]

    # 1. Return 12 units first
    payload1 = SalesReturnCreateRequest(
        sales_order_id=so_id,
        items=[
            SalesReturnItemCreateRequest(
                product_id=prod_id,
                qty=12.0,
                condition=ReturnItemConditionEnum.RESELLABLE,
            )
        ],
    )
    service.create_return(payload=payload1, current_user=dummy_admin_user)

    # 2. Try to return 10 more units (12 + 10 = 22 > 20) -> Blocked
    payload2 = SalesReturnCreateRequest(
        sales_order_id=so_id,
        items=[
            SalesReturnItemCreateRequest(
                product_id=prod_id,
                qty=10.0,
                condition=ReturnItemConditionEnum.RESELLABLE,
            )
        ],
    )
    with pytest.raises(HTTPException) as exc_info:
        service.create_return(payload=payload2, current_user=dummy_admin_user)

    assert exc_info.value.status_code == 422
    assert "maximum returnable quantity on order 'SO-202608-0001' is 8.0" in exc_info.value.detail


def test_approve_resellable_return_increases_stock_by_exact_qty(
    sales_return_setup, dummy_admin_user
):
    """QA: Approving a resellable return increases on-hand stock by exactly the returned quantity."""
    service: SalesReturnService = sales_return_setup["service"]
    stock_repo: InMemoryStockRepository = sales_return_setup["stock_repo"]
    so_id = sales_return_setup["so_id"]
    prod_id = sales_return_setup["prod_id"]
    batch_id = sales_return_setup["batch_id"]

    initial_batch_qty = stock_repo.batches[batch_id]["quantity"]  # 30.0

    # 1. Create return for 6 resellable units
    payload = SalesReturnCreateRequest(
        sales_order_id=so_id,
        items=[
            SalesReturnItemCreateRequest(
                product_id=prod_id,
                batch_id=batch_id,
                qty=6.0,
                condition=ReturnItemConditionEnum.RESELLABLE,
            )
        ],
    )
    created = service.create_return(payload=payload, current_user=dummy_admin_user)

    # Stock should NOT have changed yet while status is REQUESTED
    assert stock_repo.batches[batch_id]["quantity"] == initial_batch_qty

    # 2. Approve return
    approved = service.approve_return(return_id=created.id, current_user=dummy_admin_user)
    assert approved.status == SalesReturnStatusEnum.APPROVED

    # 3. Verify stock increased by exactly 6.0 units
    new_batch_qty = stock_repo.batches[batch_id]["quantity"]
    assert new_batch_qty == initial_batch_qty + 6.0

    # 4. Verify RETURN_IN ledger entry created
    return_in_movements = [
        m for m in stock_repo.movements if m.get("type") == StockMovementTypeEnum.RETURN_IN
    ]
    assert len(return_in_movements) == 1
    assert return_in_movements[0]["quantity"] == 6.0
    assert return_in_movements[0]["reference_id"] == created.id
    assert return_in_movements[0]["reference_type"] == "sales_return"


def test_approve_damaged_return_does_not_increase_sellable_stock(
    sales_return_setup, dummy_admin_user
):
    """QA: A damaged-condition return does NOT increase sellable stock, but is visible in return record."""
    service: SalesReturnService = sales_return_setup["service"]
    stock_repo: InMemoryStockRepository = sales_return_setup["stock_repo"]
    so_id = sales_return_setup["so_id"]
    prod_id = sales_return_setup["prod_id"]
    batch_id = sales_return_setup["batch_id"]

    initial_batch_qty = stock_repo.batches[batch_id]["quantity"]  # 30.0

    # 1. Create return for 4 DAMAGED units

    payload = SalesReturnCreateRequest(
        sales_order_id=so_id,
        items=[
            SalesReturnItemCreateRequest(
                product_id=prod_id,
                batch_id=batch_id,
                qty=4.0,
                condition=ReturnItemConditionEnum.DAMAGED,
                reason="Torn packaging during transit",
            )
        ],
    )
    created = service.create_return(payload=payload, current_user=dummy_admin_user)

    # 2. Approve return
    approved = service.approve_return(return_id=created.id, current_user=dummy_admin_user)
    assert approved.status == SalesReturnStatusEnum.APPROVED
    assert approved.items[0].condition == ReturnItemConditionEnum.DAMAGED

    # 3. Sellable stock must REMAIN UNCHANGED
    assert stock_repo.batches[batch_id]["quantity"] == initial_batch_qty
    # No RETURN_IN movement added to sellable stock
    return_in_movements = [
        m for m in stock_repo.movements if m.get("type") == StockMovementTypeEnum.RETURN_IN
    ]
    assert len(return_in_movements) == 0

    # 4. But return record is fully preserved for loss tracking
    fetched = service.get_return(created.id)
    assert len(fetched.items) == 1
    assert fetched.items[0].qty == 4.0
    assert fetched.items[0].condition == ReturnItemConditionEnum.DAMAGED


def test_reject_sales_return_leaves_stock_untouched(sales_return_setup, dummy_admin_user):
    """Test rejecting an RMA In return leaves stock completely unchanged."""
    service: SalesReturnService = sales_return_setup["service"]
    stock_repo: InMemoryStockRepository = sales_return_setup["stock_repo"]
    so_id = sales_return_setup["so_id"]
    prod_id = sales_return_setup["prod_id"]
    batch_id = sales_return_setup["batch_id"]

    initial_qty = stock_repo.batches[batch_id]["quantity"]

    payload = SalesReturnCreateRequest(
        sales_order_id=so_id,
        items=[
            SalesReturnItemCreateRequest(
                product_id=prod_id,
                qty=3.0,
                condition=ReturnItemConditionEnum.RESELLABLE,
            )
        ],
    )
    created = service.create_return(payload=payload, current_user=dummy_admin_user)

    rejected = service.reject_return(
        return_id=created.id,
        reason="Past 30-day return window",
        current_user=dummy_admin_user,
    )
    assert rejected.status == SalesReturnStatusEnum.REJECTED
    assert stock_repo.batches[batch_id]["quantity"] == initial_qty


def test_sales_returns_api_router_lifecycle(sales_return_setup, dummy_admin_user):
    """Integration test verifying FastAPI /sales-returns router endpoints."""
    service: SalesReturnService = sales_return_setup["service"]
    so_id = sales_return_setup["so_id"]
    prod_id = sales_return_setup["prod_id"]

    app.dependency_overrides[get_sales_return_service] = lambda: service
    app.dependency_overrides[get_current_user] = lambda: dummy_admin_user

    try:
        client = TestClient(app)

        # 1. POST /sales-returns
        post_resp = client.post(
            "/sales-returns",
            json={
                "sales_order_id": so_id,
                "reason": "Retailer excess stock",
                "items": [
                    {
                        "product_id": prod_id,
                        "qty": 5.0,
                        "condition": "resellable",
                    }
                ],
            },
        )
        assert post_resp.status_code == 201
        data = post_resp.json()
        return_id = data["id"]
        assert data["status"] == "requested"

        # 2. GET /sales-returns
        list_resp = client.get("/sales-returns")
        assert list_resp.status_code == 200
        assert len(list_resp.json()) >= 1

        # 3. GET /sales-returns/{id}
        get_resp = client.get(f"/sales-returns/{return_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == return_id

        # 4. PATCH /sales-returns/{id}/approve
        approve_resp = client.patch(f"/sales-returns/{return_id}/approve")
        assert approve_resp.status_code == 200
        assert approve_resp.json()["status"] == "approved"

    finally:
        app.dependency_overrides.clear()
