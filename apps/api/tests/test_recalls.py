"""Tests for Batch Recall & Defect Traceability (Step 9.3)."""

from datetime import UTC, datetime

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.api.routers.stock import router as stock_router
from app.core.security import CurrentUser, get_current_user
from app.models.inventory import StockMovementTypeEnum
from app.models.recalls import RecallSeverityEnum, RecallStatusEnum
from app.repositories.impl.audit_repository import InMemoryAuditRepository
from app.repositories.impl.recall_repository import InMemoryRecallRepository
from app.repositories.impl.stock_repository import InMemoryStockRepository
from app.schemas.recalls import BatchRecallCreateRequest
from app.services.recall_service import RecallService


@pytest.fixture
def test_data():
    """Setup product, warehouse, 2 batches, 4 sales orders, and movements."""
    products = [
        {
            "id": "prod-1",
            "name": "Almond Milk 1L",
            "sku": "ALM-MLK-001",
            "wholesale_price": 120.0,
            "cost_price": 80.0,
        },
        {
            "id": "prod-2",
            "name": "Soy Milk 1L",
            "sku": "SOY-MLK-001",
            "wholesale_price": 100.0,
            "cost_price": 70.0,
        },
    ]

    warehouses = [
        {"id": "wh-1", "name": "Main Cold Hub", "is_active": True},
    ]

    batches = [
        {
            "id": "batch-defective",
            "product_id": "prod-1",
            "warehouse_id": "wh-1",
            "batch_no": "BATCH-DEFECTIVE-999",
            "quantity": 50.0,
            "expiry_date": None,
        },
        {
            "id": "batch-clean",
            "product_id": "prod-1",
            "warehouse_id": "wh-1",
            "batch_no": "BATCH-CLEAN-111",
            "quantity": 200.0,
            "expiry_date": None,
        },
    ]

    retailers = [
        {
            "id": "ret-1",
            "name": "Fresh Mart Retail",
            "phone": "+919876543210",
            "email": "freshmart@example.com",
            "credit_limit": 50000.0,
            "credit_balance": 1000.0,
        },
        {
            "id": "ret-2",
            "name": "Green Grocers",
            "phone": "+919876543211",
            "email": "greengrocers@example.com",
            "credit_limit": 40000.0,
            "credit_balance": 2000.0,
        },
    ]

    customers = [
        {
            "id": "cust-1",
            "name": "Ananya Sharma",
            "phone": "+919876543212",
            "email": "ananya@example.com",
        }
    ]

    orders = [
        {
            "id": "so-1",
            "buyer_type": "retailer",
            "retailer_id": "ret-1",
            "customer_id": None,
            "created_at": datetime.now(UTC),
        },
        {
            "id": "so-2",
            "buyer_type": "retailer",
            "retailer_id": "ret-2",
            "customer_id": None,
            "created_at": datetime.now(UTC),
        },
        {
            "id": "so-3",
            "buyer_type": "customer",
            "retailer_id": None,
            "customer_id": "cust-1",
            "created_at": datetime.now(UTC),
        },
        {
            "id": "so-4-unaffected",
            "buyer_type": "retailer",
            "retailer_id": "ret-1",
            "customer_id": None,
            "created_at": datetime.now(UTC),
        },
    ]

    # Movements: so-1, so-2, so-3 drew from batch-defective; so-4 drew from batch-clean
    movements = [
        {
            "id": "mov-1",
            "batch_id": "batch-defective",
            "product_id": "prod-1",
            "warehouse_id": "wh-1",
            "type": StockMovementTypeEnum.OUT,
            "quantity": 10.0,
            "reference_type": "sales_order",
            "reference_id": "so-1",
        },
        {
            "id": "mov-2",
            "batch_id": "batch-defective",
            "product_id": "prod-1",
            "warehouse_id": "wh-1",
            "type": StockMovementTypeEnum.OUT,
            "quantity": 25.0,
            "reference_type": "sales_order",
            "reference_id": "so-2",
        },
        {
            "id": "mov-3",
            "batch_id": "batch-defective",
            "product_id": "prod-1",
            "warehouse_id": "wh-1",
            "type": StockMovementTypeEnum.OUT,
            "quantity": 5.0,
            "reference_type": "sales_order",
            "reference_id": "so-3",
        },
        {
            "id": "mov-4-other",
            "batch_id": "batch-clean",
            "product_id": "prod-1",
            "warehouse_id": "wh-1",
            "type": StockMovementTypeEnum.OUT,
            "quantity": 30.0,
            "reference_type": "sales_order",
            "reference_id": "so-4-unaffected",
        },
    ]

    return {
        "products": products,
        "warehouses": warehouses,
        "batches": batches,
        "retailers": retailers,
        "customers": customers,
        "orders": orders,
        "movements": movements,
    }


def test_recall_traces_exact_affected_orders(test_data):
    """
    QA Checklist: Initiating a recall on a batch with 3 known affected orders
    correctly traces all 3 and no others.
    """
    recall_repo = InMemoryRecallRepository(
        products=test_data["products"],
        warehouses=test_data["warehouses"],
        batches=test_data["batches"],
        retailers=test_data["retailers"],
        customers=test_data["customers"],
        orders=test_data["orders"],
        movements=test_data["movements"],
    )
    stock_repo = InMemoryStockRepository(
        products=test_data["products"],
        warehouses=test_data["warehouses"],
        batches=test_data["batches"],
    )
    audit_repo = InMemoryAuditRepository()

    service = RecallService(recall_repo=recall_repo, stock_repo=stock_repo, audit_repo=audit_repo)

    req = BatchRecallCreateRequest(
        batch_id="batch-defective",
        reason="Quality breach: packaging seal compromise",
        severity=RecallSeverityEnum.CRITICAL,
    )
    user = CurrentUser(id="admin-1", email="admin@wareflow.io", role="Owner", permissions={"all"})

    recall_res = service.initiate_recall(req, user)

    assert recall_res.batch_id == "batch-defective"
    assert recall_res.status == RecallStatusEnum.INITIATED
    assert recall_res.severity == RecallSeverityEnum.CRITICAL
    assert recall_res.affected_orders_count == 3

    # Verify traced orders contain so-1, so-2, so-3 and NOT so-4-unaffected
    traced_so_ids = {item.sales_order_id for item in recall_res.affected_orders}
    assert traced_so_ids == {"so-1", "so-2", "so-3"}
    assert "so-4-unaffected" not in traced_so_ids

    # Check retailer / customer names populated
    buyer_names = {item.buyer_name for item in recall_res.affected_orders}
    assert "Fresh Mart Retail" in buyer_names
    assert "Green Grocers" in buyer_names
    assert "Ananya Sharma" in buyer_names


def test_recalled_batch_excluded_from_new_sales(test_data):
    """
    QA Checklist: The recalled batch's remaining stock is excluded from new sales
    immediately, without being deleted from history.
    """
    recall_repo = InMemoryRecallRepository(
        products=test_data["products"],
        warehouses=test_data["warehouses"],
        batches=test_data["batches"],
        retailers=test_data["retailers"],
        customers=test_data["customers"],
        orders=test_data["orders"],
        movements=test_data["movements"],
    )
    stock_repo = InMemoryStockRepository(
        products=test_data["products"],
        warehouses=test_data["warehouses"],
        batches=test_data["batches"],
    )
    service = RecallService(recall_repo=recall_repo, stock_repo=stock_repo)

    user = CurrentUser(id="admin-1", email="admin@wareflow.io", role="Owner", permissions={"all"})

    # Before recall, total stock for prod-1 = 50 (batch-defective) + 200 (batch-clean) = 250
    # Deducting 220 units would succeed before recall
    # Initiate recall on batch-defective
    req = BatchRecallCreateRequest(
        batch_id="batch-defective",
        reason="Foreign particle contamination",
        severity=RecallSeverityEnum.CRITICAL,
    )
    service.initiate_recall(req, user)

    # Now only batch-clean (200 units) is available. Trying to deduct 220 should fail with shortfall
    with pytest.raises(ValueError, match="Insufficient stock"):
        stock_repo.deduct_stock_fifo(product_id="prod-1", quantity=220.0)

    # Deducting 150 units succeeds by consuming strictly from batch-clean
    deductions = stock_repo.deduct_stock_fifo(product_id="prod-1", quantity=150.0)
    assert len(deductions) == 1
    assert deductions[0][0].id == "batch-clean"

    # Historical batch-defective still exists with its 50 units intact (not deleted)
    defective_batch = stock_repo.get_batch_by_id("batch-defective")
    assert defective_batch is not None
    assert defective_batch.quantity == 50.0


def test_notify_affected_retailers_lifecycle(test_data):
    """
    QA Checklist: Notifying fires alerts to each affected retailer, and the recall's
    affected-orders list shows notified_at populated per retailer as they go out.
    """
    recall_repo = InMemoryRecallRepository(
        products=test_data["products"],
        warehouses=test_data["warehouses"],
        batches=test_data["batches"],
        retailers=test_data["retailers"],
        customers=test_data["customers"],
        orders=test_data["orders"],
        movements=test_data["movements"],
    )
    stock_repo = InMemoryStockRepository(
        products=test_data["products"],
        warehouses=test_data["warehouses"],
        batches=test_data["batches"],
    )
    service = RecallService(recall_repo=recall_repo, stock_repo=stock_repo)
    user = CurrentUser(id="admin-1", email="admin@wareflow.io", role="Owner", permissions={"all"})

    # Initiate recall
    req = BatchRecallCreateRequest(
        batch_id="batch-defective",
        reason="Packaging seal breach",
        severity=RecallSeverityEnum.MEDIUM,
    )
    recall = service.initiate_recall(req, user)

    # All affected orders initially have notified_at = None
    for aff in recall.affected_orders:
        assert aff.notified_at is None

    # Broadcast notification
    notify_res = service.notify_affected_retailers(recall.id, user)
    assert notify_res.status == RecallStatusEnum.NOTIFYING
    assert notify_res.retailers_notified_count == 2
    assert notify_res.customers_notified_count == 1

    # Check updated recall details
    updated_recall = service.get_recall_details(recall.id)
    assert updated_recall.status == RecallStatusEnum.NOTIFYING
    for aff in updated_recall.affected_orders:
        assert aff.notified_at is not None

    # Resolve recall
    resolved = service.resolve_recall(recall.id, user)
    assert resolved.status == RecallStatusEnum.RESOLVED
    assert resolved.resolved_at is not None


def test_http_recall_endpoints(test_data):
    """Integration tests for FastAPI endpoints under /stock/recalls."""
    recall_repo = InMemoryRecallRepository(
        products=test_data["products"],
        warehouses=test_data["warehouses"],
        batches=test_data["batches"],
        retailers=test_data["retailers"],
        customers=test_data["customers"],
        orders=test_data["orders"],
        movements=test_data["movements"],
    )
    stock_repo = InMemoryStockRepository(
        products=test_data["products"],
        warehouses=test_data["warehouses"],
        batches=test_data["batches"],
    )
    audit_repo = InMemoryAuditRepository()
    service = RecallService(recall_repo=recall_repo, stock_repo=stock_repo, audit_repo=audit_repo)

    app = FastAPI()
    app.include_router(stock_router)

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id="user-123", email="tester@wareflow.io", role="Admin", permissions={"all"}
    )

    from app.api.routers.stock import get_recall_service

    app.dependency_overrides[get_recall_service] = lambda: service

    client = TestClient(app)

    # 1. POST /stock/recalls
    create_resp = client.post(
        "/stock/recalls",
        json={
            "batch_id": "batch-defective",
            "reason": "Chemical residue exceeding safety thresholds",
            "severity": "critical",
        },
    )
    assert create_resp.status_code == status.HTTP_201_CREATED
    data = create_resp.json()
    recall_id = data["id"]
    assert data["batch_no"] == "BATCH-DEFECTIVE-999"
    assert data["affected_orders_count"] == 3

    # 2. GET /stock/recalls
    list_resp = client.get("/stock/recalls")
    assert list_resp.status_code == status.HTTP_200_OK
    assert list_resp.json()["total"] == 1

    # 3. GET /stock/recalls/{id}
    detail_resp = client.get(f"/stock/recalls/{recall_id}")
    assert detail_resp.status_code == status.HTTP_200_OK
    assert len(detail_resp.json()["affected_orders"]) == 3

    # 4. PATCH /stock/recalls/{id}/notify
    notify_resp = client.patch(f"/stock/recalls/{recall_id}/notify")
    assert notify_resp.status_code == status.HTTP_200_OK
    assert notify_resp.json()["status"] == "notifying"

    # 5. PATCH /stock/recalls/{id}/resolve
    resolve_resp = client.patch(f"/stock/recalls/{recall_id}/resolve")
    assert resolve_resp.status_code == status.HTTP_200_OK
    assert resolve_resp.json()["status"] == "resolved"

    # 6. Sample / Demo Recall Fallback Tests (rec-1)
    sample_get = client.get("/stock/recalls/rec-1")
    assert sample_get.status_code == status.HTTP_200_OK
    assert sample_get.json()["id"] == "rec-1"
    assert sample_get.json()["batch_no"] == "BATCH-2026-0801"

    sample_notify = client.patch("/stock/recalls/rec-1/notify")
    assert sample_notify.status_code == status.HTTP_200_OK
    assert sample_notify.json()["status"] == "notifying"
    assert sample_notify.json()["retailers_notified_count"] == 2

    sample_resolve = client.patch("/stock/recalls/rec-1/resolve")
    assert sample_resolve.status_code == status.HTTP_200_OK
    assert sample_resolve.json()["status"] == "resolved"
