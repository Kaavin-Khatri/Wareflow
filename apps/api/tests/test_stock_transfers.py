"""Tests for Inter-Warehouse Stock Transfers (Step 9.2)."""

from datetime import UTC, datetime

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.api.routers.stock import router as stock_router
from app.core.security import CurrentUser, get_current_user
from app.models.inventory import StockMovementTypeEnum
from app.repositories.impl.audit_repository import InMemoryAuditRepository
from app.repositories.impl.transfer_repository import InMemoryTransferRepository
from app.schemas.stock_transfers import StockTransferCreateRequest
from app.services.transfer_service import TransferService


@pytest.fixture
def sample_data():
    warehouses = [
        {"id": "wh-central", "name": "Central Distribution Center", "is_active": True},
        {"id": "wh-north", "name": "North Logistics Hub", "is_active": True},
    ]
    products = [
        {"id": "prod-1", "name": "Organic Whole Milk 1L", "sku": "MILK-ORG-001", "reorder_point": 20},
        {"id": "prod-2", "name": "Basmati Rice 5kg", "sku": "RIC-BAS-005", "reorder_point": 10},
    ]
    batches = [
        {
            "id": "batch-1",
            "product_id": "prod-1",
            "warehouse_id": "wh-central",
            "batch_no": "B-2026-001",
            "quantity": 100.0,
            "expiry_date": None,
            "received_at": datetime.now(UTC),
        },
        {
            "id": "batch-2",
            "product_id": "prod-2",
            "warehouse_id": "wh-central",
            "batch_no": "B-2026-002",
            "quantity": 15.0,
            "expiry_date": None,
            "received_at": datetime.now(UTC),
        },
    ]
    return warehouses, products, batches


@pytest.fixture
def transfer_repo(sample_data):
    warehouses, products, batches = sample_data
    return InMemoryTransferRepository(warehouses=warehouses, products=products, batches=batches)


@pytest.fixture
def audit_repo():
    return InMemoryAuditRepository()


@pytest.fixture
def transfer_service(transfer_repo, audit_repo):
    return TransferService(transfer_repo=transfer_repo, audit_repo=audit_repo)


def test_transfer_insufficient_source_stock_blocked(transfer_service: TransferService, transfer_repo: InMemoryTransferRepository):
    """A transfer exceeding source stock is blocked with 422 and creates zero movements."""
    user = CurrentUser(
        id="user-admin",
        email="admin@wareflow.io",
        role="Admin",
        permissions={"inventory:manage"},
    )

    # Batch-2 has only 15.0 available; try to transfer 25.0
    req = StockTransferCreateRequest(
        product_id="prod-2",
        batch_id="batch-2",
        from_warehouse_id="wh-central",
        to_warehouse_id="wh-north",
        quantity=25.0,
        notes="Transfer over stock",
    )

    with pytest.raises(Exception) as exc_info:
        transfer_service.execute_transfer(req, user)

    assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "insufficient" in str(exc_info.value.detail).lower()

    # Verify zero movements created and source batch quantity untouched
    assert len(transfer_repo.movements) == 0
    assert transfer_repo.batches["batch-2"]["quantity"] == 15.0


def test_transfer_same_warehouse_blocked(transfer_service: TransferService):
    """Transfer between same source and destination warehouse is rejected with 400."""
    user = CurrentUser(
        id="user-admin",
        email="admin@wareflow.io",
        role="Admin",
        permissions={"inventory:manage"},
    )

    req = StockTransferCreateRequest(
        product_id="prod-1",
        batch_id="batch-1",
        from_warehouse_id="wh-central",
        to_warehouse_id="wh-central",
        quantity=10.0,
        notes="Same warehouse move",
    )

    with pytest.raises(Exception) as exc_info:
        transfer_service.execute_transfer(req, user)

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "same" in str(exc_info.value.detail).lower()


def test_successful_transfer_atomic_source_and_destination_quantities(
    transfer_service: TransferService, transfer_repo: InMemoryTransferRepository, audit_repo: InMemoryAuditRepository
):
    """A successful transfer decreases source total and increases destination total by exactly the same quantity."""
    user = CurrentUser(
        id="user-admin",
        email="admin@wareflow.io",
        role="Admin",
        permissions={"inventory:manage"},
    )

    req = StockTransferCreateRequest(
        product_id="prod-1",
        batch_id="batch-1",
        from_warehouse_id="wh-central",
        to_warehouse_id="wh-north",
        quantity=40.0,
        notes="Replenishing North Logistics Hub",
    )

    res = transfer_service.execute_transfer(req, user)
    assert res.quantity == 40.0
    assert res.from_warehouse_id == "wh-central"
    assert res.to_warehouse_id == "wh-north"

    # Source batch quantity decreased by 40.0 (100 -> 60)
    assert transfer_repo.batches["batch-1"]["quantity"] == 60.0

    # Destination batch created in wh-north with 40.0
    dest_batches = [
        b for b in transfer_repo.batches.values()
        if b["warehouse_id"] == "wh-north" and b["product_id"] == "prod-1"
    ]
    assert len(dest_batches) == 1
    assert dest_batches[0]["quantity"] == 40.0
    assert dest_batches[0]["batch_no"] == "B-2026-001"

    # Exactly 2 movements written: 1 OUT and 1 IN with identical quantity magnitude
    assert len(transfer_repo.movements) == 2
    out_m = next(m for m in transfer_repo.movements if m["type"] == StockMovementTypeEnum.OUT)
    in_m = next(m for m in transfer_repo.movements if m["type"] == StockMovementTypeEnum.IN)

    assert out_m["quantity"] == -40.0
    assert out_m["warehouse_id"] == "wh-central"
    assert in_m["quantity"] == 40.0
    assert in_m["warehouse_id"] == "wh-north"
    assert out_m["reference_type"] == "warehouse_transfer"
    assert in_m["reference_type"] == "warehouse_transfer"

    # Audit log created
    assert len(audit_repo.logs) == 1
    assert audit_repo.logs[0].action == "stock_transferred"


def test_transfer_to_existing_destination_batch_increments_existing_quantity(
    transfer_service: TransferService, transfer_repo: InMemoryTransferRepository
):
    """Transfer to destination warehouse that already has the same batch_no tops up the existing batch."""
    user = CurrentUser(
        id="user-admin",
        email="admin@wareflow.io",
        role="Admin",
        permissions={"inventory:manage"},
    )

    # Pre-seed destination batch in wh-north
    transfer_repo.batches["batch-north-existing"] = {
        "id": "batch-north-existing",
        "product_id": "prod-1",
        "warehouse_id": "wh-north",
        "batch_no": "B-2026-001",
        "quantity": 10.0,
        "expiry_date": None,
        "received_at": datetime.now(UTC),
    }

    req = StockTransferCreateRequest(
        product_id="prod-1",
        batch_id="batch-1",
        from_warehouse_id="wh-central",
        to_warehouse_id="wh-north",
        quantity=30.0,
        notes="Topping up existing batch",
    )

    res = transfer_service.execute_transfer(req, user)
    assert res.destination_batch_id == "batch-north-existing"
    assert transfer_repo.batches["batch-north-existing"]["quantity"] == 40.0
    assert transfer_repo.batches["batch-1"]["quantity"] == 70.0


def test_http_endpoints_stock_transfers(transfer_service: TransferService):
    """Verify HTTP API endpoints for POST and GET /stock/transfers."""
    app = FastAPI()
    app.include_router(stock_router)

    admin_user = CurrentUser(
        id="admin-1",
        email="admin@wareflow.io",
        role="Owner",
        permissions={"inventory:view", "inventory:manage"},
    )

    app.dependency_overrides[get_current_user] = lambda: admin_user
    from app.api.routers.stock import get_transfer_service

    app.dependency_overrides[get_transfer_service] = lambda: transfer_service

    client = TestClient(app)

    # 1. Post transfer
    res = client.post(
        "/stock/transfers",
        json={
            "product_id": "prod-1",
            "batch_id": "batch-1",
            "from_warehouse_id": "wh-central",
            "to_warehouse_id": "wh-north",
            "quantity": 15.0,
            "notes": "Regional replenishment",
        },
    )
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    assert data["quantity"] == 15.0
    assert data["from_warehouse_id"] == "wh-central"
    assert data["to_warehouse_id"] == "wh-north"

    # 2. Get transfers list
    res_list = client.get("/stock/transfers")
    assert res_list.status_code == status.HTTP_200_OK
    list_data = res_list.json()
    assert list_data["total"] >= 1
    assert list_data["items"][0]["quantity"] == 15.0
    assert list_data["items"][0]["from_warehouse_name"] == "Central Distribution Center"
