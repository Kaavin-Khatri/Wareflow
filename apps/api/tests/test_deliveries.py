"""Tests for Delivery Assignment & Logistics Status Board (Step 12.1)."""

import uuid
from datetime import UTC, datetime

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.di import get_delivery_service, get_sales_order_service
from app.core.security import CurrentUser, get_current_user, require_permission
from app.main import app
from app.models.delivery import DeliveryStatusEnum
from app.models.retailer import BuyerTypeEnum, Retailer, SalesOrder, SOStatusEnum
from app.repositories.impl.delivery_repository import InMemoryDeliveryRepository
from app.repositories.impl.notification_repository import InMemoryNotificationRepository
from app.repositories.impl.retailer_repository import InMemoryRetailerRepository
from app.repositories.impl.sales_order_repository import InMemorySalesOrderRepository
from app.schemas.deliveries import DeliveryAssignRequest, DeliveryStatusUpdateRequest
from app.services.delivery_service import DeliveryService
from app.services.notification_service import NotificationService


@pytest.fixture
def test_user():
    return CurrentUser(
        id="user-staff-1",
        email="ops@wareflow.com",
        role="Admin",
        permissions={"inventory:manage"},
    )


@pytest.fixture
def setup_repos():
    retailer = Retailer(
        id="ret-1",
        name="Alpha Mart",
        contact_person="Alice",
        phone="+919876543210",
        email="alpha@mart.com",
        address="Mumbai, Maharashtra",
        credit_limit=50000.0,
        credit_balance=0.0,
    )
    retailer_repo = InMemoryRetailerRepository([retailer])
    so_repo = InMemorySalesOrderRepository()
    delivery_repo = InMemoryDeliveryRepository()
    notif_repo = InMemoryNotificationRepository()
    notif_service = NotificationService(notification_repo=notif_repo)

    delivery_service = DeliveryService(
        delivery_repo=delivery_repo,
        sales_order_repo=so_repo,
        notification_service=notif_service,
    )
    return {
        "retailer_repo": retailer_repo,
        "so_repo": so_repo,
        "delivery_repo": delivery_repo,
        "notif_repo": notif_repo,
        "delivery_service": delivery_service,
    }


def test_assign_delivery_to_non_packed_order_is_blocked(setup_repos, test_user):
    """QA Gate: Assigning a delivery to a draft or confirmed order is blocked."""
    so_repo = setup_repos["so_repo"]
    service = setup_repos["delivery_service"]

    # Create draft order
    draft_order = SalesOrder(
        id="so-draft-1",
        so_number="SO-2026-0001",
        buyer_type=BuyerTypeEnum.RETAILER,
        retailer_id="ret-1",
        status=SOStatusEnum.DRAFT,
        total_amount=1500.0,
        created_at=datetime.now(UTC),
    )
    so_repo.create(draft_order)

    # Attempt assignment on draft
    with pytest.raises(HTTPException) as exc_info:
        service.assign_delivery(
            sales_order_id="so-draft-1",
            payload=DeliveryAssignRequest(driver_name="Ramesh Kumar", vehicle_no="MH-02-AB-1234"),
            current_user=test_user,
        )
    assert exc_info.value.status_code == 422
    assert "order must be packed" in exc_info.value.detail

    # Test on confirmed order (not packed yet)
    confirmed_order = SalesOrder(
        id="so-conf-1",
        so_number="SO-2026-0002",
        buyer_type=BuyerTypeEnum.RETAILER,
        retailer_id="ret-1",
        status=SOStatusEnum.CONFIRMED,
        total_amount=2500.0,
        created_at=datetime.now(UTC),
    )
    so_repo.create(confirmed_order)

    with pytest.raises(HTTPException) as exc_info:
        service.assign_delivery(
            sales_order_id="so-conf-1",
            payload=DeliveryAssignRequest(driver_name="Ramesh Kumar", vehicle_no="MH-02-AB-1234"),
            current_user=test_user,
        )
    assert exc_info.value.status_code == 422
    assert "order must be packed" in exc_info.value.detail


def test_assign_delivery_to_packed_order_succeeds_and_advances_to_shipped(setup_repos, test_user):
    """QA Gate: Assigning a packed order creates delivery in 'assigned' status and advances order to shipped."""
    so_repo = setup_repos["so_repo"]
    service = setup_repos["delivery_service"]

    packed_order = SalesOrder(
        id="so-packed-1",
        so_number="SO-2026-0003",
        buyer_type=BuyerTypeEnum.RETAILER,
        retailer_id="ret-1",
        status=SOStatusEnum.PACKED,
        total_amount=4200.0,
        created_at=datetime.now(UTC),
    )
    so_repo.create(packed_order)

    res = service.assign_delivery(
        sales_order_id="so-packed-1",
        payload=DeliveryAssignRequest(
            driver_name="Suresh Patil",
            vehicle_no="MH-01-XY-9999",
            notes="Handle tea boxes with care",
        ),
        current_user=test_user,
    )

    assert res.id is not None
    assert res.sales_order_id == "so-packed-1"
    assert res.driver_name == "Suresh Patil"
    assert res.vehicle_no == "MH-01-XY-9999"
    assert res.status == DeliveryStatusEnum.ASSIGNED

    # Verify parent sales order was advanced to SHIPPED
    order_in_db = so_repo.get_by_id("so-packed-1")
    assert order_in_db.status == SOStatusEnum.SHIPPED


def test_out_for_delivery_records_dispatch_timestamp(setup_repos, test_user):
    """Transitioning status to out_for_delivery sets dispatched_at timestamp."""
    so_repo = setup_repos["so_repo"]
    service = setup_repos["delivery_service"]

    packed_order = SalesOrder(
        id="so-packed-2",
        so_number="SO-2026-0004",
        buyer_type=BuyerTypeEnum.RETAILER,
        retailer_id="ret-1",
        status=SOStatusEnum.PACKED,
        total_amount=3000.0,
        created_at=datetime.now(UTC),
    )
    so_repo.create(packed_order)

    delivery_res = service.assign_delivery(
        sales_order_id="so-packed-2",
        payload=DeliveryAssignRequest(driver_name="Amit Singh", vehicle_no="DL-03-CD-5678"),
        current_user=test_user,
    )

    updated = service.update_delivery_status(
        delivery_id=delivery_res.id,
        payload=DeliveryStatusUpdateRequest(status=DeliveryStatusEnum.OUT_FOR_DELIVERY),
        current_user=test_user,
    )

    assert updated.status == DeliveryStatusEnum.OUT_FOR_DELIVERY
    assert updated.dispatched_at is not None


def test_delivered_status_auto_advances_parent_sales_order(setup_repos, test_user):
    """QA Gate: Marking a delivery delivered correctly flips the parent sales order to delivered."""
    so_repo = setup_repos["so_repo"]
    service = setup_repos["delivery_service"]

    order = SalesOrder(
        id="so-packed-3",
        so_number="SO-2026-0005",
        buyer_type=BuyerTypeEnum.RETAILER,
        retailer_id="ret-1",
        status=SOStatusEnum.PACKED,
        total_amount=5000.0,
        created_at=datetime.now(UTC),
    )
    so_repo.create(order)

    delivery = service.assign_delivery(
        sales_order_id="so-packed-3",
        payload=DeliveryAssignRequest(driver_name="Kishore Kumar", vehicle_no="KA-05-AA-1111"),
        current_user=test_user,
    )

    # Deliver order
    delivered_res = service.update_delivery_status(
        delivery_id=delivery.id,
        payload=DeliveryStatusUpdateRequest(status=DeliveryStatusEnum.DELIVERED),
        current_user=test_user,
    )

    assert delivered_res.status == DeliveryStatusEnum.DELIVERED
    assert delivered_res.delivered_at is not None

    # Parent sales order must be DELIVERED
    order_in_db = so_repo.get_by_id("so-packed-3")
    assert order_in_db.status == SOStatusEnum.DELIVERED


def test_failed_delivery_requires_notes_and_keeps_order_shipped(setup_repos, test_user):
    """QA Gate: A failed delivery requires notes and does not falsely mark the order complete."""
    so_repo = setup_repos["so_repo"]
    service = setup_repos["delivery_service"]
    notif_repo = setup_repos["notif_repo"]

    order = SalesOrder(
        id="so-packed-4",
        so_number="SO-2026-0006",
        buyer_type=BuyerTypeEnum.RETAILER,
        retailer_id="ret-1",
        status=SOStatusEnum.PACKED,
        total_amount=7200.0,
        created_at=datetime.now(UTC),
    )
    so_repo.create(order)

    delivery = service.assign_delivery(
        sales_order_id="so-packed-4",
        payload=DeliveryAssignRequest(driver_name="Rajesh Sharma", vehicle_no="MH-04-QQ-4444"),
        current_user=test_user,
    )

    # Attempt failure without notes -> 422
    with pytest.raises(HTTPException) as exc_info:
        service.update_delivery_status(
            delivery_id=delivery.id,
            payload=DeliveryStatusUpdateRequest(status=DeliveryStatusEnum.FAILED, notes=""),
            current_user=test_user,
        )
    assert exc_info.value.status_code == 422
    assert "requires a notes field" in exc_info.value.detail

    # Provide valid failure reason
    failed_res = service.update_delivery_status(
        delivery_id=delivery.id,
        payload=DeliveryStatusUpdateRequest(
            status=DeliveryStatusEnum.FAILED,
            notes="Retailer shop closed for holiday, reschedule for tomorrow morning",
        ),
        current_user=test_user,
    )

    assert failed_res.status == DeliveryStatusEnum.FAILED
    assert "Retailer shop closed" in failed_res.notes

    # Parent order remains SHIPPED (not DELIVERED)
    order_in_db = so_repo.get_by_id("so-packed-4")
    assert order_in_db.status == SOStatusEnum.SHIPPED

    # Check notification was dispatched
    notifications = notif_repo.list_for_user("ret-1")
    assert len(notifications) >= 1
    assert "Delivery Failed" in notifications[0].title


def test_delivery_http_endpoints_integration(setup_repos, test_user):
    """Test HTTP endpoints for delivery assignment, board listing, and status transitions."""
    so_repo = setup_repos["so_repo"]
    delivery_service = setup_repos["delivery_service"]

    packed_order = SalesOrder(
        id="so-http-1",
        so_number="SO-2026-0888",
        buyer_type=BuyerTypeEnum.RETAILER,
        retailer_id="ret-1",
        status=SOStatusEnum.PACKED,
        total_amount=3500.0,
        created_at=datetime.now(UTC),
    )
    so_repo.create(packed_order)

    # Setup dependency overrides
    app.dependency_overrides[get_delivery_service] = lambda: delivery_service
    app.dependency_overrides[get_current_user] = lambda: test_user
    app.dependency_overrides[require_permission("inventory:manage")] = lambda: test_user

    client = TestClient(app)

    try:
        # 1. POST /sales-orders/{id}/delivery
        assign_res = client.post(
            "/sales-orders/so-http-1/delivery",
            json={
                "driver_name": "Deepak Verma",
                "vehicle_no": "MH-12-DE-7788",
                "notes": "Fragile items included",
            },
        )
        assert assign_res.status_code == 201
        data = assign_res.json()
        assert data["sales_order_id"] == "so-http-1"
        assert data["driver_name"] == "Deepak Verma"
        assert data["status"] == "assigned"
        delivery_id = data["id"]

        # 2. GET /deliveries
        list_res = client.get("/deliveries")
        assert list_res.status_code == 200
        items = list_res.json()
        assert len(items) >= 1
        assert any(d["id"] == delivery_id for d in items)

        # 3. GET /deliveries/{id}
        get_res = client.get(f"/deliveries/{delivery_id}")
        assert get_res.status_code == 200
        assert get_res.json()["vehicle_no"] == "MH-12-DE-7788"

        # 4. PATCH /deliveries/{id}/status -> out_for_delivery
        patch_res = client.patch(
            f"/deliveries/{delivery_id}/status",
            json={"status": "out_for_delivery"},
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["status"] == "out_for_delivery"

        # 5. PATCH /deliveries/{id}/status -> delivered
        deliver_res = client.patch(
            f"/deliveries/{delivery_id}/status",
            json={"status": "delivered"},
        )
        assert deliver_res.status_code == 200
        assert deliver_res.json()["status"] == "delivered"

        # 6. Check GET /sales-orders/{id}/delivery
        so_delivery_res = client.get("/sales-orders/so-http-1/delivery")
        assert so_delivery_res.status_code == 200
        assert so_delivery_res.json()["status"] == "delivered"

    finally:
        app.dependency_overrides.clear()
