"""Tests for Step 13.5 Supplier Ready-for-Dispatch Magic Link Signal & Owner Notification."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.di import get_supplier_portal_service
from app.main import app
from app.models.auth_rbac import Role
from app.models.catalog import Product
from app.models.portal import SupplierAccessToken
from app.models.profile import Profile
from app.models.supplier import POStatusEnum, PurchaseOrder, PurchaseOrderItem, Supplier
from app.repositories.impl.notification_repository import InMemoryNotificationRepository
from app.repositories.impl.profile_repository import InMemoryProfileRepository
from app.repositories.impl.purchase_order_repository import InMemoryPurchaseOrderRepository
from app.repositories.impl.supplier_access_token_repository import (
    InMemorySupplierAccessTokenRepository,
)
from app.repositories.impl.supplier_repository import InMemorySupplierRepository
from app.services.notification_channels.base import BaseNotificationChannel, NotificationPayload
from app.services.notification_service import NotificationService
from app.services.purchase_order_service import PurchaseOrderService
from app.services.supplier_portal_service import SupplierPortalService


class MockNotificationChannel(BaseNotificationChannel):
    def __init__(self, name: str) -> None:
        self._name = name
        self.sent: list[NotificationPayload] = []

    @property
    def channel_name(self) -> str:
        return self._name

    def send(self, payload: NotificationPayload) -> bool:
        self.sent.append(payload)
        return True


class MockProductRepo:
    def __init__(self, products: list[Product] | None = None) -> None:
        self.products = {p.id: p for p in (products or [])}

    def get_by_id(self, product_id: str) -> Product | None:
        return self.products.get(product_id)

    def list_all(self, *args: Any, **kwargs: Any) -> list[Product]:
        return list(self.products.values())


class MockStockService:
    def receive_stock(self, *args: Any, **kwargs: Any) -> None:
        pass


@pytest.fixture
def supplier_fixture():
    return Supplier(
        id="sup-tata-01",
        name="Tata Consumer Products Ltd",
        contact_person="Rajesh Sharma",
        phone="+919876543210",
        email="rajesh@tataconsumer.com",
        is_active=True,
    )


@pytest.fixture
def product_fixture():
    return Product(
        id="prod-tea-500g",
        name="Tata Tea Gold 500g",
        sku="TEA-GOLD-500",
        cost_price=220.0,
        unit="Pouch",
        is_active=True,
    )


@pytest.fixture
def po_fixture(supplier_fixture, product_fixture):
    po = PurchaseOrder(
        id="po-101",
        po_number="PO-202608-0101",
        supplier_id=supplier_fixture.id,
        status=POStatusEnum.ORDERED,
        total_amount=2200.0,
        order_date=datetime.now(UTC),
        expected_date=datetime.now(UTC).date() + timedelta(days=3),
    )
    po.supplier = supplier_fixture
    item = PurchaseOrderItem(
        id="item-01",
        po_id=po.id,
        product_id=product_fixture.id,
        qty_ordered=10.0,
        qty_received=0.0,
        unit_cost=220.0,
    )
    item.product = product_fixture
    po.items = [item]
    return po


@pytest.fixture
def staff_fixture():
    role = Role(id="role-owner", name="Owner")
    profile = Profile(
        id="user-owner-01",
        email="owner@wareflow.io",
        display_name="Khatri Distributor Owner",
        phone="+919999988888",
        role_id=role.id,
        is_active=True,
    )
    profile.role = role
    return profile, role


def test_supplier_portal_token_generation_and_validation(supplier_fixture, po_fixture):
    token_repo = InMemorySupplierAccessTokenRepository()
    po_repo = InMemoryPurchaseOrderRepository(pos=[po_fixture])

    service = SupplierPortalService(
        token_repo=token_repo,
        po_repo=po_repo,
    )

    token_obj = service.generate_access_token(
        supplier_id=supplier_fixture.id,
        purchase_order_id=po_fixture.id,
        expiry_days=30,
    )

    assert token_obj.token is not None
    assert len(token_obj.token) >= 32
    assert token_obj.supplier_id == supplier_fixture.id
    assert token_obj.purchase_order_id == po_fixture.id

    # Retrieve PO representation via valid token
    po_resp = service.get_po_by_token(token_obj.token)
    assert po_resp.po_number == po_fixture.po_number
    assert po_resp.supplier_name == supplier_fixture.name
    assert len(po_resp.items) == 1
    assert po_resp.items[0].product_name == "Tata Tea Gold 500g"
    assert po_resp.items[0].qty_ordered == 10.0


def test_supplier_portal_expired_token_handling(supplier_fixture, po_fixture):
    token_repo = InMemorySupplierAccessTokenRepository()
    po_repo = InMemoryPurchaseOrderRepository(pos=[po_fixture])

    service = SupplierPortalService(
        token_repo=token_repo,
        po_repo=po_repo,
    )

    expired_token = SupplierAccessToken(
        id=str(uuid.uuid4()),
        supplier_id=supplier_fixture.id,
        purchase_order_id=po_fixture.id,
        token="expired-token-123",
        expires_at=datetime.now(UTC) - timedelta(days=1),
        created_at=datetime.now(UTC) - timedelta(days=31),
    )
    token_repo.create(expired_token)

    with pytest.raises(Exception) as exc_info:
        service.get_po_by_token("expired-token-123")
    assert "410" in str(exc_info.value) or "expired" in str(exc_info.value).lower()


def test_supplier_portal_mark_ready_for_dispatch_flow(
    supplier_fixture, po_fixture, staff_fixture
):
    token_repo = InMemorySupplierAccessTokenRepository()
    po_repo = InMemoryPurchaseOrderRepository(pos=[po_fixture])

    profile, role = staff_fixture
    profile_repo = InMemoryProfileRepository(
        initial_profiles=[profile],
        initial_roles=[role],
        initial_role_permissions={role.id: ["inventory:manage", "orders:manage"]},
    )

    notif_repo = InMemoryNotificationRepository()
    wa_channel = MockNotificationChannel("whatsapp")
    email_channel = MockNotificationChannel("email")
    notif_service = NotificationService(
        notification_repo=notif_repo,
        channels=[wa_channel, email_channel],
    )

    portal_service = SupplierPortalService(
        token_repo=token_repo,
        po_repo=po_repo,
        profile_repo=profile_repo,
        notification_service=notif_service,
    )

    token_obj = portal_service.generate_access_token(
        supplier_id=supplier_fixture.id,
        purchase_order_id=po_fixture.id,
    )

    # 1. Supplier clicks mark ready for dispatch
    res = portal_service.mark_ready_for_dispatch(token_obj.token)
    assert res.success is True
    assert res.status == "ready_for_dispatch"
    assert po_fixture.status == POStatusEnum.READY_FOR_DISPATCH

    # 2. Token should be invalidated immediately (single-use)
    assert token_repo.get_by_token(token_obj.token) is None

    # 3. Subsequent attempt with same token fails
    with pytest.raises(HTTPException):
        portal_service.mark_ready_for_dispatch(token_obj.token)

    # 4. Multi-channel notifications delivered to purchasing staff / owner
    assert len(email_channel.sent) == 1
    assert len(wa_channel.sent) == 1
    assert "Ready for Dispatch" in wa_channel.sent[0].title
    assert po_fixture.po_number in wa_channel.sent[0].metadata["po_number"]


def test_po_service_auto_generates_token_on_ordered(
    supplier_fixture, product_fixture
):
    draft_po = PurchaseOrder(
        id="po-draft-01",
        po_number="PO-202608-0001",
        supplier_id=supplier_fixture.id,
        status=POStatusEnum.DRAFT,
        total_amount=2200.0,
    )
    draft_po.supplier = supplier_fixture
    item = PurchaseOrderItem(
        id="item-01",
        po_id=draft_po.id,
        product_id=product_fixture.id,
        qty_ordered=10.0,
        qty_received=0.0,
        unit_cost=220.0,
    )
    draft_po.items = [item]

    po_repo = InMemoryPurchaseOrderRepository(pos=[draft_po])
    supplier_repo = InMemorySupplierRepository([supplier_fixture])
    product_repo = MockProductRepo([product_fixture])
    token_repo = InMemorySupplierAccessTokenRepository()
    portal_service = SupplierPortalService(token_repo=token_repo, po_repo=po_repo)

    po_service = PurchaseOrderService(
        po_repo=po_repo,
        supplier_repo=supplier_repo,
        product_repo=product_repo,
        stock_service=MockStockService(),
        supplier_portal_service=portal_service,
        token_repo=token_repo,
    )

    # Transition PO to ORDERED
    resp = po_service.transition_to_ordered(draft_po.id)
    assert resp.status == POStatusEnum.ORDERED
    assert resp.magic_link_token is not None

    # Token exists in repository
    token_in_db = token_repo.get_by_purchase_order_id(draft_po.id)
    assert token_in_db is not None
    assert token_in_db.token == resp.magic_link_token


def test_public_supplier_portal_http_endpoints(supplier_fixture, po_fixture):
    token_repo = InMemorySupplierAccessTokenRepository()
    po_repo = InMemoryPurchaseOrderRepository(pos=[po_fixture])

    notif_repo = InMemoryNotificationRepository()
    notif_service = NotificationService(notification_repo=notif_repo)
    portal_service = SupplierPortalService(
        token_repo=token_repo,
        po_repo=po_repo,
        notification_service=notif_service,
    )

    token_obj = portal_service.generate_access_token(
        supplier_id=supplier_fixture.id,
        purchase_order_id=po_fixture.id,
    )

    app.dependency_overrides[get_supplier_portal_service] = lambda: portal_service
    client = TestClient(app)

    try:
        # GET /supplier-portal/{token} (Unauthenticated)
        resp = client.get(f"/supplier-portal/{token_obj.token}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["po_number"] == po_fixture.po_number
        assert data["supplier_name"] == supplier_fixture.name
        assert len(data["items"]) == 1

        # POST /supplier-portal/{token}/ready-for-dispatch (Unauthenticated)
        post_resp = client.post(f"/supplier-portal/{token_obj.token}/ready-for-dispatch")
        assert post_resp.status_code == 200
        post_data = post_resp.json()
        assert post_data["success"] is True
        assert post_data["status"] == "ready_for_dispatch"

        # Subsequent GET should return 404 since token was invalidated
        invalid_resp = client.get(f"/supplier-portal/{token_obj.token}")
        assert invalid_resp.status_code == 404
    finally:
        app.dependency_overrides.clear()
