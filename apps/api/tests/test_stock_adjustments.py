"""Tests for Stock Adjustments and Movement Ledger (Step 9.1)."""

from datetime import UTC, datetime

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.api.routers.stock import router as stock_router
from app.core.security import CurrentUser, get_current_user
from app.models.inventory import StockMovementTypeEnum
from app.repositories.impl.audit_repository import InMemoryAuditRepository
from app.repositories.impl.stock_repository import InMemoryStockRepository
from app.schemas.stock_adjustments import (
    AdjustmentReasonEnum,
    StockAdjustmentCreateRequest,
)
from app.services.stock_service import StockService


@pytest.fixture
def sample_data():
    warehouses = [
        {"id": "wh-1", "name": "Central Distribution Center", "is_active": True},
        {"id": "wh-2", "name": "West Coast Warehouse", "is_active": True},
    ]
    products = [
        {"id": "prod-1", "name": "Organic Whole Milk 1L", "sku": "MILK-ORG-001", "reorder_point": 20},
        {"id": "prod-2", "name": "Basmati Rice 5kg", "sku": "RIC-BAS-005", "reorder_point": 10},
    ]
    batches = [
        {
            "id": "batch-1",
            "product_id": "prod-1",
            "warehouse_id": "wh-1",
            "batch_no": "B-2026-001",
            "quantity": 50.0,
            "expiry_date": None,
            "received_at": datetime.now(UTC),
        },
        {
            "id": "batch-2",
            "product_id": "prod-2",
            "warehouse_id": "wh-1",
            "batch_no": "B-2026-002",
            "quantity": 15.0,
            "expiry_date": None,
            "received_at": datetime.now(UTC),
        },
    ]
    return warehouses, products, batches


@pytest.fixture
def stock_repo(sample_data):
    warehouses, products, batches = sample_data
    return InMemoryStockRepository(warehouses=warehouses, products=products, batches=batches)


@pytest.fixture
def audit_repo():
    return InMemoryAuditRepository()


@pytest.fixture
def stock_service(stock_repo, audit_repo):
    return StockService(stock_repo=stock_repo, audit_repo=audit_repo)


def test_stock_adjustment_damage_and_loss_decrease(stock_service: StockService, stock_repo: InMemoryStockRepository):
    """Warehouse staff records damage adjustment decrements batch and creates movement."""
    user = CurrentUser(
        id="user-staff",
        email="staff@wareflow.io",
        role="Warehouse Staff",
        permissions={"inventory:view", "inventory:manage"},
    )

    req = StockAdjustmentCreateRequest(
        product_id="prod-1",
        warehouse_id="wh-1",
        batch_id="batch-1",
        delta=-5.0,
        reason=AdjustmentReasonEnum.DAMAGE,
        notes="Damaged packaging during forklift transit",
    )

    res = stock_service.adjust_stock(req, user)
    assert res.previous_quantity == 50.0
    assert res.new_quantity == 45.0
    assert res.delta == -5.0
    assert res.reason == AdjustmentReasonEnum.DAMAGE

    # Check batch in repo
    assert stock_repo.batches["batch-1"]["quantity"] == 45.0

    # Check movement
    assert len(stock_repo.movements) == 1
    mov = stock_repo.movements[0]
    assert mov["type"] == StockMovementTypeEnum.ADJUSTMENT
    assert mov["quantity"] == -5.0
    assert mov["reference_type"] == "manual_adjustment"
    assert "damage" in mov["reference_id"]


def test_stock_adjustment_negative_balance_blocked(stock_service: StockService):
    """Adjustment that pushes batch below 0 is rejected with 422."""
    user = CurrentUser(
        id="user-admin",
        email="admin@wareflow.io",
        role="Admin",
        permissions={"inventory:manage"},
    )

    # Batch-2 has 15.0 quantity; try delta -20.0
    req = StockAdjustmentCreateRequest(
        product_id="prod-2",
        warehouse_id="wh-1",
        batch_id="batch-2",
        delta=-20.0,
        reason=AdjustmentReasonEnum.LOSS,
        notes="Shrinkage",
    )

    with pytest.raises(Exception) as exc_info:
        stock_service.adjust_stock(req, user)

    assert "negative" in str(exc_info.value.detail).lower()
    assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_stock_recount_permission_guard(stock_service: StockService):
    """Recount adjustment requires 'stock.recount' permission; unauthorized user gets 403."""
    # User without recount permission
    regular_user = CurrentUser(
        id="user-staff",
        email="staff@wareflow.io",
        role="Warehouse Staff",
        permissions={"inventory:manage"},
    )

    req = StockAdjustmentCreateRequest(
        product_id="prod-1",
        warehouse_id="wh-1",
        batch_id="batch-1",
        delta=10.0,
        reason=AdjustmentReasonEnum.RECOUNT,
        notes="Physical stock take recount",
    )

    with pytest.raises(Exception) as exc_info:
        stock_service.adjust_stock(req, regular_user)

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "stock.recount" in exc_info.value.detail

    # User WITH recount permission
    manager_user = CurrentUser(
        id="user-mgr",
        email="manager@wareflow.io",
        role="Manager",
        permissions={"inventory:manage", "stock:recount"},
    )

    res = stock_service.adjust_stock(req, manager_user)
    assert res.new_quantity == 60.0
    assert res.delta == 10.0


def test_stock_movement_ledger_human_labels(stock_service: StockService, stock_repo: InMemoryStockRepository):
    """Verify movements ledger generates accurate human labels for PO, SO, Return, and Adjustment."""
    # Simulate diverse movements
    stock_repo.movements.extend([
        {
            "id": "mov-po",
            "product_id": "prod-1",
            "warehouse_id": "wh-1",
            "batch_id": "batch-1",
            "type": StockMovementTypeEnum.IN,
            "quantity": 100.0,
            "reference_type": "purchase_order",
            "reference_id": "PO-202608-0001",
            "created_by": "buyer@wareflow.io",
            "created_at": datetime(2026, 8, 1, 10, 0, tzinfo=UTC),
        },
        {
            "id": "mov-so",
            "product_id": "prod-1",
            "warehouse_id": "wh-1",
            "batch_id": "batch-1",
            "type": StockMovementTypeEnum.OUT,
            "quantity": -20.0,
            "reference_type": "sales_order",
            "reference_id": "SO-202608-0002",
            "created_by": "sales@wareflow.io",
            "created_at": datetime(2026, 8, 5, 14, 0, tzinfo=UTC),
        },
        {
            "id": "mov-cancel",
            "product_id": "prod-1",
            "warehouse_id": "wh-1",
            "batch_id": "batch-1",
            "type": StockMovementTypeEnum.ADJUSTMENT,
            "quantity": 20.0,
            "reference_type": "sales_order_cancellation",
            "reference_id": "SO-202608-0002",
            "created_by": "admin@wareflow.io",
            "created_at": datetime(2026, 8, 6, 9, 0, tzinfo=UTC),
        },
        {
            "id": "mov-rma",
            "product_id": "prod-1",
            "warehouse_id": "wh-1",
            "batch_id": "batch-1",
            "type": StockMovementTypeEnum.RETURN_IN,
            "quantity": 5.0,
            "reference_type": "sales_return",
            "reference_id": "RMA-202608-0003",
            "created_by": "qc@wareflow.io",
            "created_at": datetime(2026, 8, 10, 11, 0, tzinfo=UTC),
        },
        {
            "id": "mov-adj",
            "product_id": "prod-1",
            "warehouse_id": "wh-1",
            "batch_id": "batch-1",
            "type": StockMovementTypeEnum.ADJUSTMENT,
            "quantity": -3.0,
            "reference_type": "manual_adjustment",
            "reference_id": "damage:Water leak in aisle 3",
            "created_by": "staff@wareflow.io",
            "created_at": datetime(2026, 8, 15, 16, 0, tzinfo=UTC),
        },
    ])

    ledger = stock_service.list_movements(page=1, page_size=10)
    assert ledger.total == 5
    assert len(ledger.items) == 5

    labels = {item.id: item.human_label for item in ledger.items}
    assert "PO #PO-202608-0001 (Goods Receipt)" in labels["mov-po"]
    assert "SO #SO-202608-0002 (Fulfillment Dispatch)" in labels["mov-so"]
    assert "SO #SO-202608-0002 (Order Cancellation)" in labels["mov-cancel"]
    assert "RMA #RMA-202608-0003 (Retailer Return)" in labels["mov-rma"]
    assert "Adjustment: Damage (Water leak in aisle 3)" in labels["mov-adj"]


def test_http_endpoints_adjustments_and_movements(stock_service: StockService):
    """Verify HTTP API endpoints for /stock/adjustments and /stock/movements."""
    app = FastAPI()
    app.include_router(stock_router)

    admin_user = CurrentUser(
        id="admin-1",
        email="admin@wareflow.io",
        role="Owner",
        permissions={"inventory:view", "inventory:manage", "stock:recount"},
    )

    app.dependency_overrides[get_current_user] = lambda: admin_user
    from app.api.routers.stock import get_stock_service

    app.dependency_overrides[get_stock_service] = lambda: stock_service

    client = TestClient(app)

    # 1. Post adjustment
    res = client.post(
        "/stock/adjustments",
        json={
            "product_id": "prod-1",
            "warehouse_id": "wh-1",
            "batch_id": "batch-1",
            "delta": -2.0,
            "reason": "damage",
            "notes": "Crushed container",
        },
    )
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    assert data["delta"] == -2.0
    assert data["previous_quantity"] == 50.0
    assert data["new_quantity"] == 48.0

    # 2. Get movements
    res_mov = client.get("/stock/movements")
    assert res_mov.status_code == status.HTTP_200_OK
    mov_data = res_mov.json()
    assert mov_data["total"] >= 1
    assert any("Crushed container" in m["human_label"] for m in mov_data["items"])
