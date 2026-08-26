"""Unit and integration tests for Step 15.1: Owner Analytics Dashboard (KPIs + Charts)."""

from datetime import UTC, date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.di import get_owner_dashboard_service
from app.main import app
from app.models.billing import Invoice, InvoiceStatusEnum, Payment, PaymentMethodEnum
from app.models.retailer import SalesOrder, SalesOrderItem, SOStatusEnum
from app.models.supplier import POStatusEnum
from app.repositories.impl.forecast_repository import InMemoryForecastRepository
from app.repositories.impl.invoice_repository import InMemoryInvoiceRepository
from app.repositories.impl.product_repository import InMemoryProductRepository
from app.repositories.impl.purchase_order_repository import InMemoryPurchaseOrderRepository
from app.repositories.impl.sales_order_repository import InMemorySalesOrderRepository
from app.repositories.impl.stock_repository import InMemoryStockRepository
from app.repositories.impl.supplier_repository import InMemorySupplierRepository
from app.services.dead_stock_service import DeadStockService
from app.services.forecasting.moving_average import MovingAverageForecast
from app.services.forecasting_service import ForecastingService
from app.services.insight_narrator import InsightNarratorService
from app.services.owner_dashboard_service import OwnerDashboardService
from app.services.reorder_suggestion_service import ReorderSuggestionService


@pytest.fixture
def mock_owner_env():
    """Sets up an in-memory ecosystem for testing the Owner Analytics Dashboard."""
    product_repo = InMemoryProductRepository()
    stock_repo = InMemoryStockRepository()
    so_repo = InMemorySalesOrderRepository()
    po_repo = InMemoryPurchaseOrderRepository()
    invoice_repo = InMemoryInvoiceRepository()
    supplier_repo = InMemorySupplierRepository()
    forecast_repo = InMemoryForecastRepository()

    # Forecasting & Analytics Services
    moving_avg = MovingAverageForecast()
    forecasting_service = ForecastingService(
        forecast_repo=forecast_repo,
        stock_repo=stock_repo,
        product_repo=product_repo,
        strategies=[moving_avg],
        default_strategy="moving_average",
        cache_ttl_hours=24,
    )
    reorder_service = ReorderSuggestionService(
        product_repo=product_repo,
        stock_repo=stock_repo,
        forecasting_service=forecasting_service,
        supplier_repo=supplier_repo,
        po_repo=po_repo,
    )
    dead_stock_service = DeadStockService(
        product_repo=product_repo,
        stock_repo=stock_repo,
        forecast_repo=forecast_repo,
    )
    insight_narrator = InsightNarratorService(
        so_repo=so_repo,
        reorder_service=reorder_service,
        dead_stock_service=dead_stock_service,
        groq_api_key="",
        cache_ttl_days=7,
    )

    dashboard_service = OwnerDashboardService(
        sales_order_repo=so_repo,
        stock_repo=stock_repo,
        product_repo=product_repo,
        purchase_order_repo=po_repo,
        invoice_repo=invoice_repo,
        dead_stock_service=dead_stock_service,
        insight_narrator=insight_narrator,
        supplier_repo=supplier_repo,
    )

    return {
        "product_repo": product_repo,
        "stock_repo": stock_repo,
        "so_repo": so_repo,
        "po_repo": po_repo,
        "invoice_repo": invoice_repo,
        "supplier_repo": supplier_repo,
        "forecast_repo": forecast_repo,
        "dashboard_service": dashboard_service,
    }


def test_owner_dashboard_fresh_deployment_empty_state(mock_owner_env):
    """Verify that a brand-new deployment renders zeros gracefully with no NaN or crashes."""
    service: OwnerDashboardService = mock_owner_env["dashboard_service"]

    response = service.get_owner_dashboard()

    assert response.is_empty_state is True
    assert response.kpi_metrics.monthly_sales_revenue == 0.0
    assert response.kpi_metrics.monthly_inventory_value == 0.0
    assert response.kpi_metrics.monthly_inventory_units == 0.0
    assert response.kpi_metrics.total_stock_value == 0.0
    assert response.kpi_metrics.open_pos_count == 0
    assert response.kpi_metrics.open_sos_count == 0
    assert response.kpi_metrics.low_stock_count == 0
    assert response.kpi_metrics.critical_stock_count == 0
    assert response.kpi_metrics.total_outstanding_receivables == 0.0
    assert response.kpi_metrics.overdue_invoices_count == 0

    # 30-day movement series should have exactly 30 zeroed data points
    assert len(response.movement_trend_30d) == 30
    for dp in response.movement_trend_30d:
        assert dp.inbound_qty == 0.0
        assert dp.outbound_qty == 0.0

    assert response.top_fastest_moving == []
    assert response.low_stock_quick_list == []
    assert response.overdue_invoices_quick_list == []
    assert response.weekly_insight is not None


def test_owner_dashboard_kpis_and_aggregations(mock_owner_env):
    """Verify hand-calculated KPI numbers for monthly sales, stock value, open orders, and receivables."""
    env = mock_owner_env
    product_repo: InMemoryProductRepository = env["product_repo"]
    stock_repo: InMemoryStockRepository = env["stock_repo"]
    so_repo: InMemorySalesOrderRepository = env["so_repo"]
    po_repo: InMemoryPurchaseOrderRepository = env["po_repo"]
    invoice_repo: InMemoryInvoiceRepository = env["invoice_repo"]
    supplier_repo: InMemorySupplierRepository = env["supplier_repo"]
    service: OwnerDashboardService = env["dashboard_service"]

    # 1. Add Supplier & Products
    supplier_repo.create_supplier(
        {
            "id": "supp-1",
            "name": "Agro Prime Commodities Ltd",
            "gstin": "27AAACA1234A1Z5",
            "is_active": True,
        }
    )

    product_repo.create_product(
        {
            "id": "prod-rice",
            "name": "Basmati Premium Rice 25kg",
            "sku": "RIC-BAS-025",
            "cost_price": 1200.0,
            "wholesale_price": 1800.0,
            "reorder_point": 50,
            "is_active": True,
        }
    )
    product_repo.create_product(
        {
            "id": "prod-oil",
            "name": "Sunflower Refined Oil 15L",
            "sku": "OIL-SUN-015",
            "cost_price": 1500.0,
            "wholesale_price": 2100.0,
            "reorder_point": 20,
            "is_active": True,
        }
    )
    product_repo.create_product(
        {
            "id": "prod-sugar",
            "name": "Organic Sugar 50kg",
            "sku": "SUG-ORG-050",
            "cost_price": 2000.0,
            "wholesale_price": 2600.0,
            "reorder_point": 10,
            "is_active": True,
        }
    )

    # 2. Add Stock Batches:
    # prod-rice: 100 units on hand -> value = 100 * 1200 = 120,000
    # prod-oil: 10 units on hand (<= reorder_point 20 -> low_stock) -> value = 10 * 1500 = 15,000
    # prod-sugar: 0 units on hand (critical_stock) -> value = 0
    # Total Valuation = 135,000. Total units = 110.
    stock_repo.record_stock_receipt(
        product_id="prod-rice",
        warehouse_id="wh-1",
        batch_no="B-RICE-01",
        quantity=100.0,
    )
    stock_repo.record_stock_receipt(
        product_id="prod-oil",
        warehouse_id="wh-1",
        batch_no="B-OIL-01",
        quantity=10.0,
    )

    # 3. Add Sales Orders
    # SO 1: confirmed, current month, total = 54,000 (30 bags rice)
    # SO 2: draft, total = 10,000
    # Open SOs = 2 (draft, confirmed)
    so_confirmed = SalesOrder(
        id="so-conf-1",
        so_number="SO-2026-001",
        status=SOStatusEnum.CONFIRMED,
        total_amount=54000.0,
        order_date=datetime.now(UTC),
        created_at=datetime.now(UTC),
        items=[
            SalesOrderItem(
                id="so-item-1",
                so_id="so-conf-1",
                product_id="prod-rice",
                qty=30.0,
                unit_price=1800.0,
            )
        ],
    )
    so_draft = SalesOrder(
        id="so-draft-1",
        so_number="SO-2026-002",
        status=SOStatusEnum.DRAFT,
        total_amount=10000.0,
        order_date=datetime.now(UTC),
        created_at=datetime.now(UTC),
        items=[],
    )
    so_repo.create(so_confirmed)
    so_repo.create(so_draft)

    # 4. Add Purchase Orders:
    # PO 1: ordered -> open
    # PO 2: received -> not open
    po_repo.create_purchase_order(
        {"id": "po-1", "po_number": "PO-2026-01", "supplier_id": "supp-1", "status": POStatusEnum.ORDERED},
        [],
    )
    po_repo.create_purchase_order(
        {"id": "po-2", "po_number": "PO-2026-02", "supplier_id": "supp-1", "status": POStatusEnum.RECEIVED},
        [],
    )

    # 5. Add Invoices:
    # Inv 1: unpaid, invoice_date 35 days ago (OVERDUE), total 54,000, payment 20,000 -> balance = 34,000
    # Inv 2: paid, total 10,000, payment 10,000 -> balance = 0
    # Outstanding receivables = 34,000. Overdue count = 1.
    inv_overdue = Invoice(
        id="inv-1",
        invoice_no="INV/2026-27/0001",
        sales_order_id="so-conf-1",
        status=InvoiceStatusEnum.UNPAID,
        total_amount=54000.0,
        invoice_date=datetime.now(UTC) - timedelta(days=35),
        created_at=datetime.now(UTC) - timedelta(days=35),
    )
    inv_overdue.payments = [
        Payment(
            id="pay-1",
            invoice_id="inv-1",
            amount=20000.0,
            method=PaymentMethodEnum.BANK_TRANSFER,
        )
    ]
    inv_paid = Invoice(
        id="inv-2",
        invoice_no="INV/2026-27/0002",
        sales_order_id="so-conf-2",
        status=InvoiceStatusEnum.PAID,
        total_amount=10000.0,
        invoice_date=datetime.now(UTC),
        created_at=datetime.now(UTC),
    )
    inv_paid.payments = [
        Payment(
            id="pay-2",
            invoice_id="inv-2",
            amount=10000.0,
            method=PaymentMethodEnum.UPI,
        )
    ]
    invoice_repo.create_invoice(inv_overdue, [])
    invoice_repo.create_invoice(inv_paid, [])

    # Fetch Dashboard
    resp = service.get_owner_dashboard()

    assert resp.is_empty_state is False
    assert resp.kpi_metrics.monthly_sales_revenue == 54000.0
    assert resp.kpi_metrics.monthly_inventory_value == 135000.0
    assert resp.kpi_metrics.monthly_inventory_units == 110.0
    assert resp.kpi_metrics.total_stock_value == 135000.0
    assert resp.kpi_metrics.open_pos_count == 1  # only PO 1 (ordered)
    assert resp.kpi_metrics.open_sos_count == 2  # confirmed + draft
    assert resp.kpi_metrics.low_stock_count == 1  # prod-oil (10 <= 20)
    assert resp.kpi_metrics.critical_stock_count == 1  # prod-sugar (0)
    assert resp.kpi_metrics.total_outstanding_receivables == 34000.0
    assert resp.kpi_metrics.overdue_invoices_count == 1

    # Check Overdue Quick List
    assert len(resp.overdue_invoices_quick_list) == 1
    ov_item = resp.overdue_invoices_quick_list[0]
    assert ov_item.invoice_number == "INV/2026-27/0001"
    assert ov_item.balance_due == 34000.0
    assert ov_item.overdue_days == 5

    # Check Low Stock Quick List
    assert len(resp.low_stock_quick_list) == 2
    # Critical should be first
    assert resp.low_stock_quick_list[0].product_id == "prod-sugar"
    assert resp.low_stock_quick_list[0].urgency == "critical"
    assert resp.low_stock_quick_list[1].product_id == "prod-oil"
    assert resp.low_stock_quick_list[1].urgency == "high"

    # Check Top Movers
    assert len(resp.top_fastest_moving) == 1
    assert resp.top_fastest_moving[0].product_id == "prod-rice"
    assert resp.top_fastest_moving[0].units_moved == 30.0
    assert resp.top_fastest_moving[0].revenue == 54000.0


def test_owner_dashboard_30d_movement_series_aggregation(mock_owner_env):
    """Verify that daily inbound and outbound movement quantities are bucketed accurately over 30 days."""
    env = mock_owner_env
    stock_repo: InMemoryStockRepository = env["stock_repo"]
    service: OwnerDashboardService = env["dashboard_service"]

    today = date.today()
    yesterday = today - timedelta(days=1)
    two_days_ago = today - timedelta(days=2)

    # Inbound movement yesterday: 200 units
    stock_repo.record_stock_receipt(
        product_id="prod-1",
        warehouse_id="wh-1",
        batch_no="B-01",
        quantity=200.0,
    )
    # Adjust created_at to yesterday for the movement
    stock_repo.movements[-1]["created_at"] = datetime.combine(
        yesterday, datetime.min.time(), tzinfo=UTC
    )

    # Outbound movement 2 days ago: 50 units
    stock_repo.movements.append(
        {
            "id": "mov-out-1",
            "product_id": "prod-1",
            "warehouse_id": "wh-1",
            "quantity": -50.0,
            "type": "out",
            "movement_type": "out",
            "created_at": datetime.combine(two_days_ago, datetime.min.time(), tzinfo=UTC),
        }
    )

    resp = service.get_owner_dashboard()

    series = {dp.date: dp for dp in resp.movement_trend_30d}
    assert len(series) == 30
    assert series[yesterday.isoformat()].inbound_qty == 200.0
    assert series[two_days_ago.isoformat()].outbound_qty == 50.0


def test_owner_dashboard_api_endpoint(mock_owner_env):
    """FastAPI TestClient integration test for GET /analytics/dashboard."""
    from app.core.security import CurrentUser, get_current_user

    service: OwnerDashboardService = mock_owner_env["dashboard_service"]
    app.dependency_overrides[get_owner_dashboard_service] = lambda: service
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id="owner-user-1",
        email="owner@wareflow.io",
        role="Owner",
        permissions={"*"},
    )

    try:
        client = TestClient(app)
        headers = {"Authorization": "Bearer test-owner-token"}
        response = client.get("/analytics/dashboard", headers=headers)

        assert response.status_code == 200
        data = response.json()

        assert "kpi_metrics" in data
        assert "monthly_sales_revenue" in data["kpi_metrics"]
        assert "monthly_inventory_value" in data["kpi_metrics"]
        assert "open_pos_count" in data["kpi_metrics"]
        assert "movement_trend_30d" in data
        assert len(data["movement_trend_30d"]) == 30
        assert "low_stock_quick_list" in data
        assert "overdue_invoices_quick_list" in data
        assert "is_empty_state" in data
    finally:
        app.dependency_overrides.clear()
