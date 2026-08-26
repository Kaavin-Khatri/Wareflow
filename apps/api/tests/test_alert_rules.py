"""Unit and integration tests for Step 13.2 Smart Alert Rules & Engine."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.core.security import CurrentUser
from app.models.billing import Invoice, InvoiceStatusEnum
from app.models.retailer import BuyerTypeEnum, Retailer, SalesOrder, SalesOrderItem, SOStatusEnum
from app.models.warehouse import StockBatch, Warehouse
from app.repositories.impl.alert_log_repository import InMemoryAlertLogRepository
from app.repositories.impl.invoice_repository import InMemoryInvoiceRepository
from app.repositories.impl.notification_repository import InMemoryNotificationRepository
from app.repositories.impl.product_repository import InMemoryProductRepository
from app.repositories.impl.retailer_repository import InMemoryRetailerRepository
from app.repositories.impl.sales_order_repository import InMemorySalesOrderRepository
from app.repositories.impl.stock_repository import InMemoryStockRepository
from app.services.alert_engine_service import AlertEngineService
from app.services.alert_rules.critical_stock_rule import CriticalStockRule
from app.services.alert_rules.expiring_batch_rule import ExpiringBatchRule
from app.services.alert_rules.low_stock_rule import LowStockRule
from app.services.alert_rules.overdue_invoice_rule import OverdueInvoiceRule
from app.services.notification_channels.in_app_channel import InAppChannel
from app.services.notification_service import NotificationService
from app.services.pricing_strategy import PricingEngineService
from app.services.sales_order_service import SalesOrderService


@pytest.fixture
def mock_staff_user() -> CurrentUser:
    return CurrentUser(
        id="usr-staff-1",
        email="operations@wareflow.io",
        role="Manager",
        permissions={"orders:create", "orders:view", "inventory:view"},
        display_name="Operations Manager",
    )


def test_low_stock_rule_triggers_with_suggested_reorder_qty():
    """LowStockRule fires when on-hand inventory is <= reorder_point and provides reorder qty."""
    product_repo = InMemoryProductRepository()
    prod_data = {
        "id": "prod-rice-1",
        "name": "Basmati Super Kernel 25kg",
        "sku": "RIC-BAS-25K",
        "reorder_point": 100,
        "reorder_qty": 250,
        "is_active": True,
    }
    product_repo.create_product(prod_data)

    wh = Warehouse(id="wh-1", name="Central Depot", is_active=True)
    batch = StockBatch(
        id="b1",
        product_id="prod-rice-1",
        warehouse_id=wh.id,
        batch_no="B-2026-01",
        quantity=60.0,
        expiry_date=datetime.now(UTC).date() + timedelta(days=180),
    )
    stock_repo = InMemoryStockRepository(warehouses=[wh], products=[prod_data], batches=[batch])

    rule = LowStockRule()
    from app.services.alert_rules.base import AlertEvaluationContext

    ctx = AlertEvaluationContext(product_repo=product_repo, stock_repo=stock_repo, invoice_repo=None)
    results = rule.evaluate(ctx)

    assert len(results) == 1
    alert = results[0]
    assert alert.rule_name == "low_stock"
    assert alert.alert_type == "low_stock"
    assert alert.entity_id == "prod-rice-1"
    assert "Basmati Super Kernel" in alert.title
    assert "60" in alert.body
    assert "250" in alert.body
    assert alert.metadata["link"] == "/admin/purchase-orders"
    assert alert.metadata["suggested_reorder_qty"] == 250


def test_critical_stock_rule_stockout_and_low_threshold():
    """CriticalStockRule triggers emergency alerts when stock is 0 (stockout) or <= 25% reorder point."""
    product_repo = InMemoryProductRepository()
    prod_data = {
        "id": "prod-oil-1",
        "name": "Sunflower Oil 15L Tin",
        "sku": "OIL-SUN-15L",
        "reorder_point": 50,
        "reorder_qty": 100,
        "is_active": True,
    }
    product_repo.create_product(prod_data)
    wh = Warehouse(id="wh-1", name="Central Depot", is_active=True)
    stock_repo = InMemoryStockRepository(warehouses=[wh], products=[prod_data], batches=[])

    rule = CriticalStockRule()
    from app.services.alert_rules.base import AlertEvaluationContext

    ctx = AlertEvaluationContext(product_repo=product_repo, stock_repo=stock_repo, invoice_repo=None)
    results = rule.evaluate(ctx)

    assert len(results) == 1
    alert = results[0]
    assert alert.alert_type == "critical_stock"
    assert alert.metadata["is_stockout"] is True
    assert "STOCKOUT" in alert.title or "OUT OF STOCK" in alert.title


def test_expiring_batch_rule_triggers_within_30_day_window():
    """ExpiringBatchRule identifies batches expiring in <= 30 days with remaining inventory."""
    product_repo = InMemoryProductRepository()
    prod_data = {"id": "prod-milk-1", "name": "Organic Milk Powder 1kg", "sku": "MILK-1K", "is_active": True}
    product_repo.create_product(prod_data)

    wh = Warehouse(id="wh-1", name="Vashi Cold Storage", is_active=True)
    exp_date = datetime.now(UTC).date() + timedelta(days=12)
    batch = StockBatch(
        id="b-exp-1",
        product_id="prod-milk-1",
        warehouse_id=wh.id,
        batch_no="LOT-2026-AUG",
        quantity=80.0,
        expiry_date=exp_date,
    )
    stock_repo = InMemoryStockRepository(warehouses=[wh], products=[prod_data], batches=[batch])

    rule = ExpiringBatchRule(threshold_days=30)
    from app.services.alert_rules.base import AlertEvaluationContext

    ctx = AlertEvaluationContext(product_repo=product_repo, stock_repo=stock_repo, invoice_repo=None)
    results = rule.evaluate(ctx)

    assert len(results) == 1
    alert = results[0]
    assert alert.alert_type == "expiring_batch"
    assert alert.entity_id == "b-exp-1"
    assert alert.metadata["days_remaining"] == 12
    assert alert.metadata["link"] == "/admin/stock/ledger"
    assert "12 days" in alert.body


def test_overdue_invoice_rule_triggers_for_unpaid_invoices_past_due_date():
    """OverdueInvoiceRule flags unpaid invoices past due date and links to retailer AR ledger."""
    invoice_repo = InMemoryInvoiceRepository()
    retailer_repo = InMemoryRetailerRepository()

    ret = Retailer(
        id="ret-maharashtra-1",
        name="Metro Supermarkets Ltd",
        credit_limit=500000.0,
        credit_balance=85000.0,
    )
    retailer_repo.create(ret)

    so = SalesOrder(
        id="so-overdue-1",
        so_number="SO-2026-0118",
        buyer_type=BuyerTypeEnum.RETAILER,
        retailer_id=ret.id,
        status=SOStatusEnum.CONFIRMED,
        total_amount=85000.0,
    )
    invoice_repo.set_sales_order(so)

    # Invoice past due date (invoice date 20 days ago, default credit term 15 days -> 5 days overdue)
    inv = Invoice(
        id="inv-overdue-1",
        invoice_no="INV/2026-27/0118",
        sales_order_id=so.id,
        status=InvoiceStatusEnum.UNPAID,
        total_amount=85000.0,
        invoice_date=datetime.now(UTC) - timedelta(days=20),
    )
    invoice_repo.create_invoice(inv, [])

    rule = OverdueInvoiceRule()
    from app.services.alert_rules.base import AlertEvaluationContext

    ctx = AlertEvaluationContext(
        product_repo=None,
        stock_repo=None,
        invoice_repo=invoice_repo,
        retailer_repo=retailer_repo,
    )
    results = rule.evaluate(ctx)

    assert len(results) == 1
    alert = results[0]
    assert alert.alert_type == "overdue_invoice"
    assert alert.entity_id == "inv-overdue-1"
    assert alert.metadata["days_overdue"] == 5
    assert alert.metadata["amount_due"] == 85000.0
    assert alert.metadata["link"] == f"/admin/retailers/{ret.id}/ledger"
    assert "Metro Supermarkets Ltd" in alert.title
    assert "₹85,000.00" in alert.body


def test_24_hour_deduplication_guard_prevents_alert_spam():
    """Repeating the same low-stock/overdue condition within 24h does NOT re-notify."""
    alert_log_repo = InMemoryAlertLogRepository()
    notif_repo = InMemoryNotificationRepository()
    product_repo = InMemoryProductRepository()
    invoice_repo = InMemoryInvoiceRepository()

    notif_service = NotificationService(
        notification_repo=notif_repo,
        channels=[InAppChannel(notification_repo=notif_repo)],
    )

    prod_data = {
        "id": "prod-sugar-1",
        "name": "Refined Sugar M-30 50kg",
        "sku": "SUG-M30-50K",
        "reorder_point": 200,
        "reorder_qty": 500,
        "is_active": True,
    }
    product_repo.create_product(prod_data)

    wh = Warehouse(id="wh-1", name="Main Warehouse", is_active=True)
    batch = StockBatch(
        id="b-sug-1",
        product_id="prod-sugar-1",
        warehouse_id=wh.id,
        batch_no="SUG-2026",
        quantity=150.0,  # Below reorder point 200
        expiry_date=datetime.now(UTC).date() + timedelta(days=365),
    )
    stock_repo = InMemoryStockRepository(warehouses=[wh], products=[prod_data], batches=[batch])

    engine = AlertEngineService(
        alert_log_repo=alert_log_repo,
        notification_service=notif_service,
        product_repo=product_repo,
        stock_repo=stock_repo,
        invoice_repo=invoice_repo,
        dedup_window_hours=24,
    )

    # First evaluation cycle: should fire 1 alert
    fired_first = engine.evaluate_all()
    assert len(fired_first) == 1
    assert alert_log_repo.has_recent_alert("low_stock", "product", "prod-sugar-1", 24) is True
    assert len(notif_repo._notifications) == 1

    # Second evaluation cycle within 24h: must be suppressed (dedup proven)
    fired_second = engine.evaluate_all()
    assert len(fired_second) == 0
    assert len(notif_repo._notifications) == 1


def test_sales_order_confirmation_inline_triggers_low_stock_alert_instantly(mock_staff_user: CurrentUser):
    """Dropping a product below its reorder_point via a sale triggers an alert immediately within seconds."""
    alert_log_repo = InMemoryAlertLogRepository()
    notif_repo = InMemoryNotificationRepository()
    product_repo = InMemoryProductRepository()
    invoice_repo = InMemoryInvoiceRepository()
    retailer_repo = InMemoryRetailerRepository()
    so_repo = InMemorySalesOrderRepository()

    notif_service = NotificationService(
        notification_repo=notif_repo,
        channels=[InAppChannel(notification_repo=notif_repo)],
    )

    prod_data = {
        "id": "prod-tea-1",
        "name": "Assam CTC Premium Tea 1kg",
        "sku": "TEA-ASSAM-1K",
        "reorder_point": 100,
        "reorder_qty": 300,
        "wholesale_price": 450.0,
        "is_active": True,
    }
    product_repo.create_product(prod_data)

    wh = Warehouse(id="wh-1", name="Central Depot", is_active=True)
    batch = StockBatch(
        id="b-tea-1",
        product_id="prod-tea-1",
        warehouse_id=wh.id,
        batch_no="TEA-LOT-1",
        quantity=150.0,  # Initially above reorder point (150 > 100)
        expiry_date=datetime.now(UTC).date() + timedelta(days=200),
    )
    stock_repo = InMemoryStockRepository(warehouses=[wh], products=[prod_data], batches=[batch])

    alert_engine = AlertEngineService(
        alert_log_repo=alert_log_repo,
        notification_service=notif_service,
        product_repo=product_repo,
        stock_repo=stock_repo,
        invoice_repo=invoice_repo,
        dedup_window_hours=24,
    )

    ret = Retailer(
        id="ret-kirana-1",
        name="Shree Ram Kirana Store",
        credit_limit=200000.0,
        credit_balance=0.0,
    )
    retailer_repo.create(ret)

    pricing_engine = PricingEngineService()
    so_service = SalesOrderService(
        so_repo=so_repo,
        retailer_repo=retailer_repo,
        stock_repo=stock_repo,
        product_repo=product_repo,
        pricing_engine=pricing_engine,
        alert_engine=alert_engine,
    )

    # Place order for 80 bags (150 - 80 = 70 bags, which is <= reorder_point 100)
    order = SalesOrder(
        id="so-alert-test-1",
        so_number="SO-2026-TEST",
        buyer_type=BuyerTypeEnum.RETAILER,
        retailer_id=ret.id,
        status=SOStatusEnum.DRAFT,
        total_amount=36000.0,
        items=[
            SalesOrderItem(
                id=str(uuid.uuid4()),
                so_id="so-alert-test-1",
                product_id="prod-tea-1",
                qty=80.0,
                unit_price=450.0,
            )
        ],
    )
    so_repo.create(order)

    # Confirm order -> triggers FIFO stock deduction and inline smart alert
    so_service.confirm_order(order.id, mock_staff_user)

    # Verify inventory fell to 70
    assert stock_repo.get_on_hand("prod-tea-1") == 70.0

    # Verify inline alert was dispatched to notification repository instantly
    assert len(notif_repo._notifications) == 1
    notif = notif_repo._notifications[0]
    assert notif.type == "low_stock"
    assert "Assam CTC Premium Tea" in notif.title
    assert "70" in notif.body


def test_alert_scheduler_trigger_now():
    """APScheduler in-process background worker starts, executes evaluation, and shuts down."""
    from app.core.alert_scheduler import AlertScheduler

    alert_log_repo = InMemoryAlertLogRepository()
    notif_repo = InMemoryNotificationRepository()
    product_repo = InMemoryProductRepository()
    stock_repo = InMemoryStockRepository()
    invoice_repo = InMemoryInvoiceRepository()

    notif_service = NotificationService(
        notification_repo=notif_repo,
        channels=[InAppChannel(notification_repo=notif_repo)],
    )

    alert_engine = AlertEngineService(
        alert_log_repo=alert_log_repo,
        notification_service=notif_service,
        product_repo=product_repo,
        stock_repo=stock_repo,
        invoice_repo=invoice_repo,
        dedup_window_hours=24,
    )

    scheduler = AlertScheduler(alert_engine_factory=lambda: alert_engine, interval_minutes=15)
    scheduler.start()
    assert scheduler.is_running is True

    # Immediate trigger
    fired = scheduler.trigger_now()
    assert isinstance(fired, list)

    scheduler.shutdown()
    assert scheduler.is_running is False

