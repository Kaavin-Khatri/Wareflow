"""Tests for Step 13.4 Retailer Restock Subscriptions & Availability Alerts."""

from datetime import UTC, date, datetime
from typing import Any
import pytest
from fastapi.testclient import TestClient

from app.core.security import CurrentUser, get_current_user
from app.main import app
from app.models.catalog import Product
from app.models.portal import ChannelPreferenceEnum, StockSubscription
from app.models.retailer import Retailer
from app.models.supplier import POStatusEnum, PurchaseOrder, PurchaseOrderItem
from app.repositories.impl.notification_repository import InMemoryNotificationRepository
from app.repositories.impl.stock_subscription_repository import (
    InMemoryStockSubscriptionRepository,
)
from app.schemas.purchase_orders import POReceiveItemRequest, POReceiveRequest
from app.services.alert_engine_service import AlertEngineService
from app.services.alert_rules.base import AlertEvaluationContext
from app.services.alert_rules.restock_alert_rule import RestockAlertRule
from app.services.notification_channels.base import BaseNotificationChannel, NotificationPayload
from app.services.notification_service import NotificationService
from app.services.stock_subscription_service import StockSubscriptionService


class MockProductRepo:
    def __init__(self, products: list[Product] | None = None) -> None:
        self.products = {p.id: p for p in (products or [])}

    def get_by_id(self, product_id: str) -> Product | None:
        return self.products.get(product_id)

    def list_all(self, *args: Any, **kwargs: Any) -> list[Product]:
        return list(self.products.values())


class MockRetailerRepo:
    def __init__(self, retailers: list[Retailer] | None = None) -> None:
        self.retailers = {r.id: r for r in (retailers or [])}

    def get_by_id(self, retailer_id: str) -> Retailer | None:
        return self.retailers.get(retailer_id)

    def list_all(self, *args: Any, **kwargs: Any) -> list[Retailer]:
        return list(self.retailers.values())


class MockStockRepo:
    def __init__(self, stock_map: dict[str, float] | None = None) -> None:
        self.stock_map = stock_map or {}

    def get_total_stock_for_product(self, product_id: str) -> float:
        return self.stock_map.get(product_id, 0.0)


class MockChannel(BaseNotificationChannel):
    def __init__(self, name: str) -> None:
        self._name = name
        self.sent_payloads: list[NotificationPayload] = []

    @property
    def channel_name(self) -> str:
        return self._name

    def send(self, payload: NotificationPayload) -> bool:
        self.sent_payloads.append(payload)
        return True


def test_stock_subscription_lifecycle_create_reactivate_unsubscribe():
    """Test subscribing, reactivating, and unsubscribing."""
    p = Product(
        id="prod-rice-1",
        name="Basmati Rice 25kg",
        sku="RICE-BAS-25",
        unit="bags",
        reorder_point=50,
    )
    r = Retailer(
        id="ret-metro-1",
        name="Metro Cash & Carry",
        phone="+91 98765 43210",
        email="orders@metro.com",
    )

    sub_repo = InMemoryStockSubscriptionRepository()
    prod_repo = MockProductRepo([p])
    ret_repo = MockRetailerRepo([r])
    service = StockSubscriptionService(
        subscription_repo=sub_repo,
        product_repo=prod_repo,
        retailer_repo=ret_repo,
    )

    # 1. Subscribe
    sub1 = service.subscribe(
        product_id="prod-rice-1",
        retailer_id="ret-metro-1",
        channel_preference="whatsapp",
    )
    assert sub1.is_active is True
    assert sub1.channel_preference == "whatsapp"
    assert sub1.product_name == "Basmati Rice 25kg"
    assert sub1.retailer_name == "Metro Cash & Carry"

    # Verify counts
    counts = service.get_retailer_subscription_counts()
    assert counts.get("ret-metro-1") == 1

    # 2. Unsubscribe
    service.unsubscribe(product_id="prod-rice-1", retailer_id="ret-metro-1")
    assert sub_repo.get_by_id(sub1.id).is_active is False
    assert service.get_retailer_subscription_counts().get("ret-metro-1", 0) == 0

    # 3. Resubscribe (reactivates existing row)
    sub2 = service.subscribe(
        product_id="prod-rice-1",
        retailer_id="ret-metro-1",
        channel_preference="both",
    )
    assert sub2.id == sub1.id
    assert sub2.is_active is True
    assert sub2.channel_preference == "both"
    assert service.get_retailer_subscription_counts().get("ret-metro-1") == 1


def test_restock_alert_rule_notifies_subscribers_and_auto_deactivates():
    """
    Subscribing a retailer to an out-of-stock product, then receiving stock,
    dispatches exactly one notification and auto-deactivates the subscription.
    """
    p = Product(
        id="prod-sugar-1",
        name="Refined Sugar M-30 50kg",
        sku="SUGAR-M30-50",
        unit="bags",
        reorder_point=100,
    )
    r1 = Retailer(
        id="ret-reliance-1",
        name="Reliance Smart",
        phone="+91 99887 76655",
        email="procurement@reliance.com",
    )
    r2 = Retailer(
        id="ret-dmart-1",
        name="DMart Wholesale",
        phone="+91 91234 56789",
        email="buy@dmart.com",
    )

    sub_repo = InMemoryStockSubscriptionRepository()
    prod_repo = MockProductRepo([p])
    ret_repo = MockRetailerRepo([r1, r2])
    stock_repo = MockStockRepo({"prod-sugar-1": 0.0})

    notif_repo = InMemoryNotificationRepository()
    whatsapp_mock = MockChannel("whatsapp")
    email_mock = MockChannel("email")
    notif_service = NotificationService(
        notification_repo=notif_repo,
        channels=[whatsapp_mock, email_mock],
    )

    sub_service = StockSubscriptionService(
        subscription_repo=sub_repo,
        product_repo=prod_repo,
        retailer_repo=ret_repo,
    )

    # Both retailers subscribe while stock is 0
    sub_service.subscribe("prod-sugar-1", "ret-reliance-1", channel_preference="whatsapp")
    sub_service.subscribe("prod-sugar-1", "ret-dmart-1", channel_preference="both")

    assert len(sub_repo.list_active_for_product("prod-sugar-1")) == 2

    # Restock rule evaluation while stock is still 0 -> 0 alerts fired
    rule = RestockAlertRule()
    context = AlertEvaluationContext(
        product_repo=prod_repo,
        stock_repo=stock_repo,
        invoice_repo=None,
        retailer_repo=ret_repo,
        stock_subscription_repo=sub_repo,
        notification_service=notif_service,
    )
    results_zero = rule.evaluate_entity("prod-sugar-1", context)
    assert len(results_zero) == 0
    assert len(whatsapp_mock.sent_payloads) == 0

    # Stock is now received: 200 bags replenished
    stock_repo.stock_map["prod-sugar-1"] = 200.0

    # Execute restock alert rule
    results_replenished = rule.evaluate_entity("prod-sugar-1", context)
    assert len(results_replenished) == 2

    # Check WhatsApp payloads: 2 dispatched (one to Reliance, one to DMart)
    assert len(whatsapp_mock.sent_payloads) == 2
    r_payload = [pl for pl in whatsapp_mock.sent_payloads if pl.user_id == "ret-reliance-1"][0]
    assert r_payload.type == "stock_available"
    assert "Refined Sugar M-30 50kg" in r_payload.title
    assert r_payload.recipient_phone == "+91 99887 76655"

    # Check Email payloads: 1 dispatched (DMart selected 'both')
    assert len(email_mock.sent_payloads) == 1
    d_payload = email_mock.sent_payloads[0]
    assert d_payload.user_id == "ret-dmart-1"
    assert d_payload.recipient_email == "buy@dmart.com"

    # Verify auto-deactivation: subscriptions marked is_active=False
    active_remaining = sub_repo.list_active_for_product("prod-sugar-1")
    assert len(active_remaining) == 0

    # Receiving MORE stock again does NOT re-notify
    stock_repo.stock_map["prod-sugar-1"] = 500.0
    results_second = rule.evaluate_entity("prod-sugar-1", context)
    assert len(results_second) == 0
    assert len(whatsapp_mock.sent_payloads) == 2  # still 2


def test_http_subscribe_unsubscribe_and_list_endpoints():
    """Test HTTP API routes for stock subscriptions."""
    from app.core.di import get_stock_subscription_service

    client = TestClient(app)

    # Mock user dependency
    dummy_user = CurrentUser(
        id="usr-test-staff",
        email="staff@wareflow.io",
        role="Manager",
        permissions={"inventory:view", "inventory:manage", "retailers:manage"},
        is_2fa_verified=True,
    )

    sub_repo = InMemoryStockSubscriptionRepository()
    mock_service = StockSubscriptionService(
        subscription_repo=sub_repo,
        product_repo=MockProductRepo([Product(id="test-prod-1", sku="SKU-1", name="Product 1", unit="kg", reorder_point=10)]),
        retailer_repo=MockRetailerRepo([Retailer(id="test-ret-1", name="Retailer 1")]),
    )

    app.dependency_overrides[get_current_user] = lambda: dummy_user
    app.dependency_overrides[get_stock_subscription_service] = lambda: mock_service

    try:
        # 1. Subscribe
        resp_sub = client.post(
            "/products/test-prod-1/subscribe",
            json={"retailer_id": "test-ret-1", "channel_preference": "both"},
        )
        assert resp_sub.status_code == 200
        data = resp_sub.json()
        assert data["is_active"] is True
        assert data["channel_preference"] == "both"
        assert data["product_name"] == "Product 1"

        # 2. List subscribers for product
        resp_subs = client.get("/products/test-prod-1/subscribers")
        assert resp_subs.status_code == 200
        assert len(resp_subs.json()) == 1

        # 3. List subscriptions for retailer
        resp_ret_subs = client.get("/retailers/test-ret-1/subscriptions")
        assert resp_ret_subs.status_code == 200
        assert len(resp_ret_subs.json()) == 1

        # 4. Subscription counts
        resp_counts = client.get("/retailers/subscriptions/counts")
        assert resp_counts.status_code == 200
        assert resp_counts.json().get("test-ret-1") == 1

        # 5. Unsubscribe
        resp_unsub = client.delete("/products/test-prod-1/subscribe?retailer_id=test-ret-1")
        assert resp_unsub.status_code == 200
        assert resp_unsub.json().get("success") is True

        # 6. Count is now 0
        resp_counts_after = client.get("/retailers/subscriptions/counts")
        assert resp_counts_after.status_code == 200
        assert resp_counts_after.json().get("test-ret-1", 0) == 0
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_stock_subscription_service, None)


def test_stock_service_receive_stock_triggers_restock_alert_inline():
    """Test StockService.receive_stock automatically invokes AlertEngineService and sends restock alert."""
    from app.repositories.impl.stock_repository import InMemoryStockRepository
    from app.services.stock_service import StockService

    p = Product(
        id="prod-wheat-1",
        name="Sharbati Whole Wheat 50kg",
        sku="WHEAT-SHAR-50",
        unit="bags",
        reorder_point=20,
    )
    r = Retailer(
        id="ret-kirana-1",
        name="Gupta Kirana Store",
        phone="+91 98111 22233",
        email="gupta@kirana.in",
    )

    prod_repo = MockProductRepo([p])
    ret_repo = MockRetailerRepo([r])
    stock_repo = InMemoryStockRepository(
        warehouses=[{"id": "wh-main-1", "name": "Main Hub", "location": "Bhiwandi"}]
    )
    sub_repo = InMemoryStockSubscriptionRepository()

    notif_repo = InMemoryNotificationRepository()
    whatsapp_mock = MockChannel("whatsapp")
    email_mock = MockChannel("email")
    notif_service = NotificationService(
        notification_repo=notif_repo,
        channels=[whatsapp_mock, email_mock],
    )

    alert_engine = AlertEngineService(
        notification_service=notif_service,
        product_repo=prod_repo,
        stock_repo=stock_repo,
        retailer_repo=ret_repo,
        stock_subscription_repo=sub_repo,
    )

    stock_service = StockService(
        stock_repo=stock_repo,
        alert_engine=alert_engine,
    )

    sub_service = StockSubscriptionService(
        subscription_repo=sub_repo,
        product_repo=prod_repo,
        retailer_repo=ret_repo,
    )

    # 1. Retailer subscribes when stock is 0
    sub_service.subscribe("prod-wheat-1", "ret-kirana-1", channel_preference="both")
    assert len(sub_repo.list_active_for_product("prod-wheat-1")) == 1

    # 2. Receive stock for this product via stock_service.receive_stock
    stock_service.receive_stock(
        product_id="prod-wheat-1",
        warehouse_id="wh-main-1",
        batch_no="BATCH-WHEAT-2026-01",
        quantity=100.0,
    )

    # 3. Verify notification was dispatched via both channels
    assert len(whatsapp_mock.sent_payloads) == 1
    assert whatsapp_mock.sent_payloads[0].recipient_phone == "+91 98111 22233"
    assert "Sharbati Whole Wheat 50kg" in whatsapp_mock.sent_payloads[0].title

    assert len(email_mock.sent_payloads) == 1
    assert email_mock.sent_payloads[0].recipient_email == "gupta@kirana.in"

    # 4. Verify subscription was auto-deactivated
    assert len(sub_repo.list_active_for_product("prod-wheat-1")) == 0

