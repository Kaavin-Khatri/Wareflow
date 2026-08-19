"""Unit and integration tests for Step 14.3: Anomaly Detection & Owner Insight Narratives."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.security import CurrentUser, get_current_user
from app.main import app
from app.models.retailer import BuyerTypeEnum, Retailer, SalesOrder, SalesOrderItem, SOStatusEnum
from app.repositories.impl.product_repository import InMemoryProductRepository
from app.repositories.impl.purchase_order_repository import InMemoryPurchaseOrderRepository
from app.repositories.impl.retailer_repository import InMemoryRetailerRepository
from app.repositories.impl.sales_order_repository import InMemorySalesOrderRepository
from app.repositories.impl.stock_repository import InMemoryStockRepository
from app.repositories.impl.supplier_repository import InMemorySupplierRepository
from app.schemas.sales_orders import SalesOrderCreateRequest, SalesOrderItemCreateRequest
from app.services.anomaly_detection_service import AnomalyDetectionService
from app.services.dead_stock_service import DeadStockService
from app.services.forecasting.moving_average import MovingAverageForecast
from app.services.forecasting_service import ForecastingService
from app.services.insight_narrator import InsightNarratorService
from app.services.pricing_strategy import PricingEngineService
from app.services.purchase_order_service import PurchaseOrderService
from app.services.reorder_suggestion_service import ReorderSuggestionService
from app.services.sales_order_service import SalesOrderService
from app.services.stock_service import StockService
from app.services.uom_service import UomService


@pytest.fixture
def mock_owner_user() -> CurrentUser:
    return CurrentUser(
        id="usr-owner-1",
        email="owner@wareflow.in",
        role="Owner",
        permissions={"inventory:view", "inventory:manage", "inventory:create", "orders:create", "orders:view"},
        account_type="staff",
    )


def test_anomaly_detection_flags_10x_normal_quantity():
    """QA 1: A crafted 10x-normal order quantity gets flagged; a normal-range order does not."""
    # Setup historical sales orders: buyer previously ordered 10, 12, 10, 11, 10 units of product-1
    historical_orders = [
        {
            "id": f"so-hist-{i}",
            "so_number": f"SO-202601-000{i}",
            "buyer_type": BuyerTypeEnum.RETAILER,
            "retailer_id": "ret-alpha-1",
            "status": SOStatusEnum.CONFIRMED,
            "total_amount": 1000.0,
            "order_date": datetime.now(UTC) - timedelta(days=20 - i),
            "created_at": datetime.now(UTC) - timedelta(days=20 - i),
            "items": [
                {
                    "id": f"item-hist-{i}",
                    "so_id": f"so-hist-{i}",
                    "product_id": "prod-rice-25kg",
                    "qty": q,
                    "unit_price": 100.0,
                }
            ],
        }
        for i, q in enumerate([10.0, 12.0, 10.0, 11.0, 10.0])
    ]

    so_repo = InMemorySalesOrderRepository(initial_data=historical_orders)
    anomaly_service = AnomalyDetectionService(so_repo=so_repo, stddev_multiplier=3.0)

    # 1. Normal-range order: 12 units
    normal_report = anomaly_service.evaluate_line_item(
        product_id="prod-rice-25kg",
        qty=12.0,
        retailer_id="ret-alpha-1",
        product_name="Basmati Rice 25kg",
        product_sku="SKU-RICE-25KG",
    )
    assert not normal_report.is_unusual
    assert normal_report.sample_count == 5
    assert normal_report.historical_mean == 10.6
    assert normal_report.anomaly_reason is None

    # 2. Crafted 10x unusual order: 120 units
    unusual_report = anomaly_service.evaluate_line_item(
        product_id="prod-rice-25kg",
        qty=120.0,
        retailer_id="ret-alpha-1",
        product_name="Basmati Rice 25kg",
        product_sku="SKU-RICE-25KG",
    )
    assert unusual_report.is_unusual
    assert unusual_report.sample_count == 5
    assert unusual_report.historical_mean == 10.6
    assert unusual_report.threshold is not None
    assert unusual_report.qty > unusual_report.threshold
    assert "exceeds normal 3σ threshold" in (unusual_report.anomaly_reason or "")


def test_anomaly_detection_edge_cases():
    """Verify clean statistical handling for 0 prior orders, 1 prior order, and zero variance."""
    so_repo = InMemorySalesOrderRepository(initial_data=[])
    anomaly_service = AnomalyDetectionService(so_repo=so_repo, stddev_multiplier=3.0)

    # Edge Case 1: Zero prior orders -> cannot compute deviation, not flagged
    rep_zero = anomaly_service.evaluate_line_item(
        product_id="prod-new-item",
        qty=50.0,
        retailer_id="ret-new-1",
    )
    assert not rep_zero.is_unusual
    assert rep_zero.sample_count == 0
    assert rep_zero.threshold is None

    # Edge Case 2: Exactly 1 prior order (qty=10)
    so_repo.create(
        SalesOrder(
            id="so-single-1",
            so_number="SO-202601-0100",
            buyer_type=BuyerTypeEnum.RETAILER,
            retailer_id="ret-single",
            status=SOStatusEnum.CONFIRMED,
            total_amount=500.0,
            items=[SalesOrderItem(id="it-1", so_id="so-single-1", product_id="prod-item-x", qty=10.0, unit_price=50.0)],
        )
    )
    # Order of 15 is within 3x threshold
    rep_single_normal = anomaly_service.evaluate_line_item(
        product_id="prod-item-x",
        qty=15.0,
        retailer_id="ret-single",
    )
    assert not rep_single_normal.is_unusual

    # Order of 50 is > 3x previous (10 * 3 = 30) -> flagged
    rep_single_high = anomaly_service.evaluate_line_item(
        product_id="prod-item-x",
        qty=50.0,
        retailer_id="ret-single",
    )
    assert rep_single_high.is_unusual
    assert rep_single_high.threshold == 30.0


def test_sales_order_service_surfaces_anomalies_in_order_response(mock_owner_user: CurrentUser):
    """Verify that SalesOrderService integrates AnomalyDetectionService and surfaces warning flags."""
    # Setup history of 5 orders with 10 units each
    historical_orders = [
        {
            "id": f"so-h-{i}",
            "so_number": f"SO-202601-000{i}",
            "buyer_type": BuyerTypeEnum.RETAILER,
            "retailer_id": "ret-test-1",
            "status": SOStatusEnum.CONFIRMED,
            "total_amount": 1000.0,
            "order_date": datetime.now(UTC) - timedelta(days=10 - i),
            "created_at": datetime.now(UTC) - timedelta(days=10 - i),
            "items": [
                {
                    "id": f"it-h-{i}",
                    "so_id": f"so-h-{i}",
                    "product_id": "prod-oil-1l",
                    "qty": 10.0,
                    "unit_price": 100.0,
                }
            ],
        }
        for i in range(5)
    ]

    so_repo = InMemorySalesOrderRepository(initial_data=historical_orders)
    retailer_repo = InMemoryRetailerRepository()
    retailer_repo.create(
        Retailer(
            id="ret-test-1",
            name="Test Grocery Mart",
            pricing_tier="standard",
            credit_limit=500000.0,
            credit_balance=0.0,
        )
    )
    stock_repo = InMemoryStockRepository()
    product_repo = InMemoryProductRepository()
    product_repo.create_product(
        {
            "id": "prod-oil-1l",
            "sku": "SKU-OIL-1L",
            "name": "Sunflower Oil 1L",
            "cost_price": 80.0,
            "wholesale_price": 100.0,
        }
    )
    pricing_engine = PricingEngineService()
    anomaly_detector = AnomalyDetectionService(so_repo=so_repo, stddev_multiplier=3.0)

    so_service = SalesOrderService(
        so_repo=so_repo,
        retailer_repo=retailer_repo,
        stock_repo=stock_repo,
        product_repo=product_repo,
        pricing_engine=pricing_engine,
        anomaly_detector=anomaly_detector,
    )

    # Create a 100-unit order (10x normal history)
    req = SalesOrderCreateRequest(
        buyer_type=BuyerTypeEnum.RETAILER,
        retailer_id="ret-test-1",
        items=[SalesOrderItemCreateRequest(product_id="prod-oil-1l", qty=100.0, unit_price=100.0)],
    )

    created_so = so_service.create_order(payload=req, current_user=mock_owner_user)

    # Order must NOT be blocked (created as draft), but advisory flags must be present
    assert created_so.status == SOStatusEnum.DRAFT
    assert created_so.has_unusual_items
    assert created_so.unusual_items_count == 1
    assert len(created_so.anomaly_warnings) == 1
    assert created_so.items[0].is_unusual
    assert created_so.items[0].historical_mean == 10.0


def test_weekly_insight_narrator_deterministic_template_grounding():
    """QA 2 & 3: Weekly insight generates strictly grounded sentences against underlying numbers without Groq."""
    now = datetime.now(UTC)
    # 2 confirmed orders in trailing 7 days
    recent_orders = [
        {
            "id": "so-recent-1",
            "so_number": "SO-2026-001",
            "buyer_type": BuyerTypeEnum.RETAILER,
            "retailer_id": "ret-1",
            "status": SOStatusEnum.CONFIRMED,
            "total_amount": 50000.0,
            "order_date": now - timedelta(days=2),
            "created_at": now - timedelta(days=2),
            "items": [
                {
                    "id": "it-1",
                    "so_id": "so-recent-1",
                    "product_id": "prod-1",
                    "product_name": "Premium Tea 500g",
                    "qty": 100.0,
                    "unit_price": 500.0,
                }
            ],
        },
        {
            "id": "so-recent-2",
            "so_number": "SO-2026-002",
            "buyer_type": BuyerTypeEnum.RETAILER,
            "retailer_id": "ret-2",
            "status": SOStatusEnum.CONFIRMED,
            "total_amount": 25000.0,
            "order_date": now - timedelta(days=4),
            "created_at": now - timedelta(days=4),
            "items": [
                {
                    "id": "it-2",
                    "so_id": "so-recent-2",
                    "product_id": "prod-2",
                    "product_name": "Instant Coffee 200g",
                    "qty": 50.0,
                    "unit_price": 500.0,
                }
            ],
        },
    ]

    so_repo = InMemorySalesOrderRepository(initial_data=recent_orders)
    product_repo = InMemoryProductRepository()
    stock_repo = InMemoryStockRepository()
    supplier_repo = InMemorySupplierRepository()
    po_repo = InMemoryPurchaseOrderRepository()
    stock_service = StockService(stock_repo=stock_repo, uom_service=UomService(uom_repo=None))
    po_service = PurchaseOrderService(
        po_repo=po_repo,
        supplier_repo=supplier_repo,
        product_repo=product_repo,
        stock_service=stock_service,
    )
    forecasting_service = ForecastingService(
        forecast_repo=None,
        stock_repo=stock_repo,
        product_repo=product_repo,
        strategies=[MovingAverageForecast()],
    )
    reorder_service = ReorderSuggestionService(
        product_repo=product_repo,
        stock_repo=stock_repo,
        forecasting_service=forecasting_service,
        supplier_repo=supplier_repo,
        po_repo=po_repo,
        po_service=po_service,
    )
    dead_stock_service = DeadStockService(
        product_repo=product_repo,
        stock_repo=stock_repo,
        forecast_repo=None,
    )

    narrator = InsightNarratorService(
        so_repo=so_repo,
        reorder_service=reorder_service,
        dead_stock_service=dead_stock_service,
        groq_api_key="",  # Unset -> deterministic fallback
        cache_ttl_days=7,
    )

    insight = narrator.get_weekly_insight(force_refresh=True)

    # Assertions on underlying metrics
    assert insight.metrics_summary.weekly_revenue == 75000.0
    assert insight.metrics_summary.weekly_orders_count == 2
    assert insight.metrics_summary.confirmed_orders_count == 2
    assert insight.metrics_summary.top_mover_product_name == "Premium Tea 500g"
    assert insight.metrics_summary.top_mover_units_sold == 100.0

    # Assertions on narrative grounding
    assert "₹75,000" in insight.headline
    assert "₹75,000.00" in insight.narrative
    assert "2 orders" in insight.narrative
    assert "Premium Tea 500g" in insight.narrative
    assert "100 units sold" in insight.narrative
    assert not insight.is_ai_generated
    assert not insight.is_cached


def test_weekly_insight_7_day_caching_and_force_refresh():
    """Verify 7-day TTL response caching and force_refresh behavior."""
    so_repo = InMemorySalesOrderRepository(initial_data=[])
    product_repo = InMemoryProductRepository()
    stock_repo = InMemoryStockRepository()
    supplier_repo = InMemorySupplierRepository()
    po_repo = InMemoryPurchaseOrderRepository()
    stock_service = StockService(stock_repo=stock_repo, uom_service=UomService(uom_repo=None))
    po_service = PurchaseOrderService(
        po_repo=po_repo,
        supplier_repo=supplier_repo,
        product_repo=product_repo,
        stock_service=stock_service,
    )
    forecasting_service = ForecastingService(
        forecast_repo=None,
        stock_repo=stock_repo,
        product_repo=product_repo,
        strategies=[MovingAverageForecast()],
    )
    reorder_service = ReorderSuggestionService(
        product_repo=product_repo,
        stock_repo=stock_repo,
        forecasting_service=forecasting_service,
        supplier_repo=supplier_repo,
        po_repo=po_repo,
        po_service=po_service,
    )
    dead_stock_service = DeadStockService(
        product_repo=product_repo,
        stock_repo=stock_repo,
        forecast_repo=None,
    )

    narrator = InsightNarratorService(
        so_repo=so_repo,
        reorder_service=reorder_service,
        dead_stock_service=dead_stock_service,
        groq_api_key="",
        cache_ttl_days=7,
    )

    # 1. First call: compiles fresh insight (is_cached=False)
    res1 = narrator.get_weekly_insight()
    assert not res1.is_cached
    first_gen_time = res1.generated_at

    # 2. Second call within TTL: served from cache (is_cached=True)
    res2 = narrator.get_weekly_insight()
    assert res2.is_cached
    assert res2.generated_at == first_gen_time

    # 3. Force refresh call: regenerates fresh (is_cached=False)
    res3 = narrator.get_weekly_insight(force_refresh=True)
    assert not res3.is_cached


def test_api_endpoints_anomalies_and_weekly_insight(mock_owner_user: CurrentUser):
    """Test REST API routes for GET /analytics/weekly-insight and GET /analytics/anomalies/order/{id}."""
    app.dependency_overrides[get_current_user] = lambda: mock_owner_user

    with TestClient(app) as client:
        # Test weekly-insight endpoint
        resp_insight = client.get("/analytics/weekly-insight")
        assert resp_insight.status_code == 200
        data_insight = resp_insight.json()
        assert "headline" in data_insight
        assert "narrative" in data_insight
        assert "metrics_summary" in data_insight
        assert "expires_at" in data_insight

        # Test non-existent order anomalies endpoint returns 404
        resp_missing = client.get("/analytics/anomalies/order/non-existent-order-id")
        assert resp_missing.status_code == 404
