"""Tests for Step 16.3: Period Comparisons & Scheduled Weekly Owner Reports."""

from datetime import datetime, timedelta, timezone
from typing import Any
import pytest
from fastapi.testclient import TestClient

from app.core.security import CurrentUser, get_current_user
from app.main import app
from app.models.auth_rbac import Role
from app.models.billing import Invoice, InvoiceStatusEnum, Payment, PaymentMethodEnum
from app.models.catalog import Product
from app.models.profile import Profile
from app.models.retailer import SOStatusEnum, SalesOrder, SalesOrderItem
from app.models.inventory import StockMovement
from app.models.warehouse import StockBatch, Warehouse
from app.repositories.impl.business_settings_repository import (
    InMemoryBusinessSettingsRepository,
)
from app.repositories.impl.invoice_repository import InMemoryInvoiceRepository
from app.repositories.impl.notification_repository import (
    InMemoryNotificationRepository,
)
from app.repositories.impl.product_repository import InMemoryProductRepository
from app.repositories.impl.profile_repository import InMemoryProfileRepository
from app.repositories.impl.sales_order_repository import InMemorySalesOrderRepository
from app.repositories.impl.stock_repository import InMemoryStockRepository
from app.schemas.analytics import ComparisonMetricResult
from app.services.comparison_service import ComparisonService
from app.services.notification_channels.in_app_channel import InAppChannel
from app.services.notification_service import NotificationService
from app.services.scheduled_report_service import ScheduledReportService


@pytest.fixture
def mock_user() -> CurrentUser:
    return CurrentUser(
        id="usr-owner-1",
        email="owner@wareflow.in",
        role="Owner",
        permissions={"analytics:view", "settings:manage", "orders:view", "invoices:view"},
    )


@pytest.fixture
def test_data():
    now = datetime.now(timezone.utc)

    # 1. Products
    p1 = Product(id="prod-1", name="Basmati Rice 5kg", sku="RICE-5KG", cost_price=200.0, reorder_point=20)
    p2 = Product(id="prod-2", name="Refined Oil 1L", sku="OIL-1L", cost_price=100.0, reorder_point=15)
    p3 = Product(id="prod-3", name="Stagnant Spice Pack", sku="SPICE-100G", cost_price=50.0, reorder_point=5)

    prod_repo = InMemoryProductRepository([p1, p2, p3])

    # 2. Stock on hand
    wh = Warehouse(id="wh-1", name="Central Hub", is_active=True)
    batch1 = StockBatch(id="b-1", product_id="prod-1", warehouse_id="wh-1", batch_no="B01", quantity=50.0)
    batch2 = StockBatch(id="b-2", product_id="prod-2", warehouse_id="wh-1", batch_no="B02", quantity=10.0)
    batch3 = StockBatch(id="b-3", product_id="prod-3", warehouse_id="wh-1", batch_no="B03", quantity=100.0)

    stock_repo = InMemoryStockRepository(
        warehouses=[wh],
        products=[p1, p2, p3],
        batches=[batch1, batch2, batch3],
    )

    # Record damage adjustment in trailing 7 days
    _, mov, _, _ = stock_repo.record_stock_adjustment(
        "prod-1",
        "wh-1",
        "b-1",
        -2.0, # 2 * 200 = ₹400 loss
        "Damaged package",
        created_by="usr-owner-1",
    )
    if stock_repo.movements:
        stock_repo.movements[-1]["created_at"] = now - timedelta(days=2)

    # 3. Sales Orders
    # Current period (last 7d)
    so_curr = SalesOrder(
        id="so-curr-1",
        so_number="SO-101",
        retailer_id="ret-1",
        status=SOStatusEnum.CONFIRMED,
        total_amount=3000.0,
        order_date=now - timedelta(days=2),
        items=[
            SalesOrderItem(id="item-1", so_id="so-curr-1", product_id="prod-1", qty=10.0, unit_price=300.0), # Rev = 3000, Cost = 2000, Margin = 1000
        ],
    )
    # Prior period (8 to 14 days ago)
    so_prior = SalesOrder(
        id="so-prior-1",
        so_number="SO-100",
        retailer_id="ret-1",
        status=SOStatusEnum.CONFIRMED,
        total_amount=2000.0,
        order_date=now - timedelta(days=10),
        items=[
            SalesOrderItem(id="item-2", so_id="so-prior-1", product_id="prod-1", qty=8.0, unit_price=250.0), # Rev = 2000, Cost = 1600
        ],
    )

    so_repo = InMemorySalesOrderRepository([so_curr, so_prior])

    # 4. Invoices
    inv_repo = InMemoryInvoiceRepository()
    inv_overdue = Invoice(
        id="inv-1",
        invoice_no="INV-2026-001",
        sales_order_id="so-prior-1",
        total_amount=2000.0,
        status=InvoiceStatusEnum.OVERDUE,
        invoice_date=now - timedelta(days=40),
    )
    inv_overdue.payments = [
        Payment(
            id="pay-1",
            invoice_id="inv-1",
            amount=500.0,
            method=PaymentMethodEnum.BANK_TRANSFER,
        )
    ]
    inv_repo.create_invoice(inv_overdue, items=[])

    # 5. Profiles
    owner_role = Role(id="role-owner", name="Owner")
    owner_prof = Profile(
        id="usr-owner-1",
        email="owner@wareflow.in",
        role_id="role-owner",
        display_name="Rajesh Khatri",
        phone="+919876543210",
    )
    owner_prof.role = owner_role
    prof_repo = InMemoryProfileRepository(
        initial_profiles=[owner_prof],
        initial_roles=[owner_role],
    )

    # 6. Notifications
    notif_repo = InMemoryNotificationRepository()
    in_app = InAppChannel(notification_repo=notif_repo)
    notif_service = NotificationService(notification_repo=notif_repo, channels=[in_app])

    biz_repo = InMemoryBusinessSettingsRepository()

    return {
        "prod_repo": prod_repo,
        "stock_repo": stock_repo,
        "so_repo": so_repo,
        "inv_repo": inv_repo,
        "prof_repo": prof_repo,
        "notif_service": notif_service,
        "biz_repo": biz_repo,
        "now": now,
    }


def test_comparison_service_pure_math():
    """QA Item 1: Verify ComparisonService delta calculations, trends, zero-guards, and polarity inversion."""
    # 1. Positive growth
    res_growth = ComparisonService.compute_metric_delta(
        metric_key="revenue",
        metric_label="Gross Revenue",
        current=120.0,
        prior=100.0,
        higher_is_better=True,
    )
    assert res_growth.delta_value == 20.0
    assert res_growth.delta_pct == 20.0
    assert res_growth.trend == "up"
    assert res_growth.is_positive is True

    # 2. Decline
    res_decline = ComparisonService.compute_metric_delta(
        metric_key="revenue",
        metric_label="Gross Revenue",
        current=80.0,
        prior=100.0,
        higher_is_better=True,
    )
    assert res_decline.delta_value == -20.0
    assert res_decline.delta_pct == -20.0
    assert res_decline.trend == "down"
    assert res_decline.is_positive is False

    # 3. Polarity inversion (e.g. Shrinkage: down is desirable/green)
    res_shrinkage = ComparisonService.compute_metric_delta(
        metric_key="shrinkage",
        metric_label="Shrinkage",
        current=50.0,
        prior=100.0,
        higher_is_better=False,
    )
    assert res_shrinkage.delta_value == -50.0
    assert res_shrinkage.delta_pct == -50.0
    assert res_shrinkage.trend == "down"
    assert res_shrinkage.is_positive is True # favorable because higher_is_better=False

    # 4. Zero prior edge cases
    res_zero_prior = ComparisonService.compute_metric_delta(
        metric_key="revenue",
        metric_label="Revenue",
        current=500.0,
        prior=0.0,
    )
    assert res_zero_prior.delta_pct == 100.0
    assert res_zero_prior.trend == "up"

    res_both_zero = ComparisonService.compute_metric_delta(
        metric_key="revenue",
        metric_label="Revenue",
        current=0.0,
        prior=0.0,
    )
    assert res_both_zero.delta_pct == 0.0
    assert res_both_zero.trend == "flat"


def test_comparison_service_period_integration(test_data):
    """Verify ComparisonService aggregates real order and stock records accurately across windows."""
    comp_svc = ComparisonService(
        sales_order_repo=test_data["so_repo"],
        stock_repo=test_data["stock_repo"],
        product_repo=test_data["prod_repo"],
    )

    res = comp_svc.get_period_comparisons(period="7d", as_of=test_data["now"])
    assert res.period == "7d"
    assert "revenue" in res.metrics
    assert "gross_margin" in res.metrics
    assert "stock_valuation" in res.metrics
    assert "shrinkage_value" in res.metrics

    # Current 7d revenue is 3000, prior 7d revenue is 2000
    rev_metric = res.metrics["revenue"]
    assert rev_metric.current_value == 3000.0
    assert rev_metric.prior_value == 2000.0
    assert rev_metric.delta_pct == 50.0 # +50% growth
    assert rev_metric.trend == "up"

    # Shrinkage in current period is ₹400
    shrink_metric = res.metrics["shrinkage_value"]
    assert shrink_metric.current_value == 400.0


def test_scheduled_report_data_and_pdf(test_data):
    """QA Item 2: Scheduled report compilation and PDF generation."""
    comp_svc = ComparisonService(
        sales_order_repo=test_data["so_repo"],
        stock_repo=test_data["stock_repo"],
        product_repo=test_data["prod_repo"],
    )
    report_svc = ScheduledReportService(
        sales_order_repo=test_data["so_repo"],
        stock_repo=test_data["stock_repo"],
        product_repo=test_data["prod_repo"],
        invoice_repo=test_data["inv_repo"],
        profile_repo=test_data["prof_repo"],
        comparison_service=comp_svc,
        notification_service=test_data["notif_service"],
        business_settings_repo=test_data["biz_repo"],
    )

    data = report_svc.compile_weekly_report_data(as_of=test_data["now"])
    assert data.revenue_inr == 3000.0
    assert data.revenue_delta_pct == 50.0
    assert data.low_stock_count == 1 # Refined Oil is on-hand 10 <= 15
    assert data.overdue_invoices_count == 1
    assert data.overdue_amount_inr == 1500.0 # 2000 - 500
    assert data.shrinkage_inr == 400.0
    assert len(data.top_fast_movers) > 0
    assert data.top_fast_movers[0]["name"] == "Basmati Rice 5kg"

    # Generate PDF bytes
    pdf_bytes = report_svc.generate_weekly_report_pdf(as_of=test_data["now"])
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF")


def test_send_now_dispatch_and_matching_content(test_data):
    """QA Item 3: send-now produces identical summary and dispatches to notification channels."""
    comp_svc = ComparisonService(
        sales_order_repo=test_data["so_repo"],
        stock_repo=test_data["stock_repo"],
        product_repo=test_data["prod_repo"],
    )
    report_svc = ScheduledReportService(
        sales_order_repo=test_data["so_repo"],
        stock_repo=test_data["stock_repo"],
        product_repo=test_data["prod_repo"],
        invoice_repo=test_data["inv_repo"],
        profile_repo=test_data["prof_repo"],
        comparison_service=comp_svc,
        notification_service=test_data["notif_service"],
        business_settings_repo=test_data["biz_repo"],
    )

    send_res = report_svc.send_weekly_report(as_of=test_data["now"], channels=["in_app"])
    assert send_res.success is True
    assert send_res.recipients_count == 1
    assert "₹3,000" in send_res.summary_text
    assert "₹1,500" in send_res.summary_text

    # Verify notification created in repository
    notifs, total, unread = test_data["notif_service"].list_user_notifications(user_id="usr-owner-1")
    assert total == 1
    assert notifs[0].type == "weekly_report"
    assert "Weekly Business Summary" in notifs[0].title


def test_analytics_router_period_and_weekly_report_endpoints(mock_user, test_data):
    """Verify FastAPI router endpoints for period comparisons and weekly reports."""
    from app.core.di import get_comparison_service, get_scheduled_report_service

    comp_svc = ComparisonService(
        sales_order_repo=test_data["so_repo"],
        stock_repo=test_data["stock_repo"],
        product_repo=test_data["prod_repo"],
    )
    report_svc = ScheduledReportService(
        sales_order_repo=test_data["so_repo"],
        stock_repo=test_data["stock_repo"],
        product_repo=test_data["prod_repo"],
        invoice_repo=test_data["inv_repo"],
        profile_repo=test_data["prof_repo"],
        comparison_service=comp_svc,
        notification_service=test_data["notif_service"],
        business_settings_repo=test_data["biz_repo"],
    )

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_comparison_service] = lambda: comp_svc
    app.dependency_overrides[get_scheduled_report_service] = lambda: report_svc

    try:
        client = TestClient(app)

        # 1. GET /analytics/period-comparisons
        r_comp = client.get("/analytics/period-comparisons?period=7d")
        assert r_comp.status_code == 200
        comp_json = r_comp.json()
        assert comp_json["period"] == "7d"
        assert "revenue" in comp_json["metrics"]
        assert comp_json["metrics"]["revenue"]["delta_pct"] == 50.0

        # 2. GET /analytics/weekly-report/latest
        r_latest = client.get("/analytics/weekly-report/latest")
        assert r_latest.status_code == 200
        latest_json = r_latest.json()
        assert latest_json["revenue_inr"] == 3000.0
        assert latest_json["overdue_amount_inr"] == 1500.0

        # 3. GET /analytics/weekly-report/pdf
        r_pdf = client.get("/analytics/weekly-report/pdf")
        assert r_pdf.status_code == 200
        assert r_pdf.headers["content-type"] == "application/pdf"
        assert r_pdf.content.startswith(b"%PDF")

        # 4. POST /analytics/weekly-report/send-now
        r_send = client.post("/analytics/weekly-report/send-now", json={"channels": ["in_app"]})
        assert r_send.status_code == 200
        send_json = r_send.json()
        assert send_json["success"] is True
        assert send_json["recipients_count"] >= 1
    finally:
        app.dependency_overrides.clear()
