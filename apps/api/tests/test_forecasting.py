"""Unit and integration tests for Demand Forecasting Service & Pluggable Strategies (Step 14.1)."""

import uuid
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.core.di import get_forecasting_service
from app.core.security import CurrentUser, get_current_user
from app.main import create_app
from app.models.catalog import Product
from app.models.inventory import StockMovement, StockMovementTypeEnum
from app.repositories.impl.forecast_repository import InMemoryForecastRepository
from app.repositories.impl.product_repository import InMemoryProductRepository
from app.repositories.impl.stock_repository import InMemoryStockRepository
from app.services.forecasting.exponential_smoothing import ExponentialSmoothingForecast
from app.services.forecasting.moving_average import MovingAverageForecast
from app.services.forecasting_service import ForecastingService


def _create_mock_movement(
    product_id: str,
    quantity: float,
    days_ago: float,
    movement_type: StockMovementTypeEnum = StockMovementTypeEnum.OUT,
) -> StockMovement:
    """Helper to create historical stock movement timestamped N days in the past."""
    m = StockMovement(
        id=str(uuid.uuid4()),
        product_id=product_id,
        warehouse_id="wh-test-1",
        type=movement_type,
        quantity=quantity,
        reference_type="sales_order",
        reference_id="so-mock-1",
        created_by="system",
    )
    m.created_at = datetime.now(UTC) - timedelta(days=days_ago)
    return m


def test_hand_computed_forecast_moving_average_accuracy():
    """Verify exact mathematical precision of WeightedMovingAverage against hand-calculated expectations."""
    # Setup Strategy
    strategy = MovingAverageForecast()

    # Product A: 70 units every week for 4 weeks (steady demand)
    # Week 4 (25d ago): 70, Week 3 (18d ago): 70, Week 2 (11d ago): 70, Week 1 (3d ago): 70
    movements_a = [
        _create_mock_movement("prod-a", 70.0, days_ago=25),
        _create_mock_movement("prod-a", 70.0, days_ago=18),
        _create_mock_movement("prod-a", 70.0, days_ago=11),
        _create_mock_movement("prod-a", 70.0, days_ago=3),
    ]
    res_a = strategy.forecast("prod-a", movements_a, horizon_days=30)

    # Hand calculation:
    # Weighted weekly = (1*70 + 2*70 + 3*70 + 4*70)/10 = 70.0
    # Daily demand = 70.0 / 7 = 10.0
    # Total 30d demand = 10.0 * 30 = 300.0
    assert res_a.status == "calculated"
    assert res_a.predicted_daily_demand == 10.0
    assert res_a.total_predicted_demand == 300.0
    assert res_a.trend_direction == "stable"
    assert res_a.confidence_score >= 0.80

    # Product B: Increasing sales (14, 28, 42, 56)
    # Week 4 (25d ago): 14, Week 3 (18d ago): 28, Week 2 (11d ago): 42, Week 1 (3d ago): 56
    movements_b = [
        _create_mock_movement("prod-b", 14.0, days_ago=25),
        _create_mock_movement("prod-b", 28.0, days_ago=18),
        _create_mock_movement("prod-b", 42.0, days_ago=11),
        _create_mock_movement("prod-b", 56.0, days_ago=3),
    ]
    res_b = strategy.forecast("prod-b", movements_b, horizon_days=30)

    # Hand calculation:
    # Weighted weekly = (1*14 + 2*28 + 3*42 + 4*56)/10 = (14 + 56 + 126 + 224)/10 = 420 / 10 = 42.0
    # Daily demand = 42.0 / 7 = 6.0
    # Total 30d demand = 6.0 * 30 = 180.0
    assert res_b.status == "calculated"
    assert res_b.predicted_daily_demand == 6.0
    assert res_b.total_predicted_demand == 180.0
    assert res_b.trend_direction == "increasing"


def test_pluggable_strategy_swap_changes_numbers_without_touching_callers():
    """
    OCP Proof: Swapping strategy from MovingAverage to ExponentialSmoothing produces
    distinct statistical outputs without altering caller signatures.
    """
    moving_avg_strategy = MovingAverageForecast()
    exp_smooth_strategy = ExponentialSmoothingForecast(alpha=0.35)

    # Weekly history: 14, 28, 42, 56
    movements = [
        _create_mock_movement("prod-b", 14.0, days_ago=25),
        _create_mock_movement("prod-b", 28.0, days_ago=18),
        _create_mock_movement("prod-b", 42.0, days_ago=11),
        _create_mock_movement("prod-b", 56.0, days_ago=3),
    ]

    res_ma = moving_avg_strategy.forecast("prod-b", movements, horizon_days=30)
    res_es = exp_smooth_strategy.forecast("prod-b", movements, horizon_days=30)

    # Hand calculation for Exponential Smoothing (alpha=0.35):
    # S0 = 14.0
    # S1 = 0.35*28 + 0.65*14 = 9.8 + 9.1 = 18.9
    # S2 = 0.35*42 + 0.65*18.9 = 14.7 + 12.285 = 26.985
    # S3 = 0.35*56 + 0.65*26.985 = 19.6 + 17.54025 = 37.14025
    # Daily demand = 37.14025 / 7 = 5.30575 -> 5.3057 (banker's rounding)
    # Total 30d demand = 5.3057 * 30 = 159.17
    assert res_ma.predicted_daily_demand == 6.0
    assert res_ma.total_predicted_demand == 180.0

    assert res_es.predicted_daily_demand in (5.3057, 5.3058)
    assert res_es.total_predicted_demand == 159.17

    assert res_ma.total_predicted_demand != res_es.total_predicted_demand
    assert res_es.strategy == "exponential_smoothing"


def test_brand_new_product_returns_honest_insufficient_data():
    """Verify a product with no movements returns an honest 'insufficient_data' response, not fabricated numbers."""
    strategy = MovingAverageForecast()
    res = strategy.forecast("brand-new-prod", movements=[], horizon_days=30)

    assert res.status == "insufficient_data"
    assert res.predicted_daily_demand == 0.0
    assert res.total_predicted_demand == 0.0
    assert res.confidence_score == 0.0
    assert res.trend_direction == "insufficient_data"
    assert "Insufficient movement history" in (res.message or "")


def test_forecasting_service_24h_caching_and_force_refresh():
    """Verify ForecastingService caches predictions for 24h and force_refresh invalidates cache."""
    product = Product(id="prod-101", name="Basmati Rice 5kg", sku="RICE-BAS-5", is_active=True)
    product_repo = InMemoryProductRepository([product])
    stock_repo = InMemoryStockRepository()

    movements = [
        _create_mock_movement("prod-101", 70.0, days_ago=25),
        _create_mock_movement("prod-101", 70.0, days_ago=18),
        _create_mock_movement("prod-101", 70.0, days_ago=11),
        _create_mock_movement("prod-101", 70.0, days_ago=3),
    ]
    forecast_repo = InMemoryForecastRepository(
        initial_movements=movements,
        initial_products=[
            {
                "id": "prod-101",
                "name": "Basmati Rice 5kg",
                "sku": "RICE-BAS-5",
                "category": "Grains",
            }
        ],
    )

    service = ForecastingService(
        forecast_repo=forecast_repo,
        stock_repo=stock_repo,
        product_repo=product_repo,
        strategies=[MovingAverageForecast(), ExponentialSmoothingForecast()],
        default_strategy="moving_average",
        cache_ttl_hours=24,
    )

    # 1. Initial calculation: not cached
    res1 = service.get_product_forecast("prod-101", horizon_days=30)
    assert res1.is_cached is False
    assert res1.predicted_daily_demand == 10.0
    assert res1.total_predicted_demand == 300.0

    # 2. Second request: should be served from 24h cache
    res2 = service.get_product_forecast("prod-101", horizon_days=30)
    assert res2.is_cached is True
    assert res2.total_predicted_demand == 300.0

    # 3. Force refresh request: should bypass cache
    res3 = service.get_product_forecast("prod-101", horizon_days=30, force_refresh=True)
    assert res3.is_cached is False
    assert res3.total_predicted_demand == 300.0


def test_forecast_summary_ranks_top_and_slow_movers():
    """Verify get_forecast_summary compiles catalog ranking correctly."""
    prod_high = Product(id="prod-high", name="Fast Mover Oil", sku="OIL-1", is_active=True)
    prod_slow = Product(id="prod-slow", name="Slow Mover Spice", sku="SPC-1", is_active=True)
    product_repo = InMemoryProductRepository([prod_high, prod_slow])
    stock_repo = InMemoryStockRepository()

    movements = [
        _create_mock_movement("prod-high", 140.0, days_ago=3),
        _create_mock_movement("prod-slow", 7.0, days_ago=3),
    ]
    forecast_repo = InMemoryForecastRepository(
        initial_movements=movements,
        initial_products=[
            {"id": "prod-high", "name": "Fast Mover Oil", "sku": "OIL-1", "category": "Oils"},
            {"id": "prod-slow", "name": "Slow Mover Spice", "sku": "SPC-1", "category": "Spices"},
        ],
    )

    service = ForecastingService(
        forecast_repo=forecast_repo,
        stock_repo=stock_repo,
        product_repo=product_repo,
        strategies=[MovingAverageForecast()],
        default_strategy="moving_average",
    )

    summary = service.get_forecast_summary(horizon_days=30, limit=5)

    assert summary.total_products_analyzed == 2
    assert summary.total_projected_demand > 0
    assert summary.top_movers[0].product_id == "prod-high"
    assert summary.slow_movers[0].product_id == "prod-slow"


def test_api_product_forecast_and_summary_endpoints():
    """Test HTTP API routes GET /products/{id}/forecast and GET /analytics/forecast-summary."""
    product = Product(id="prod-http-1", name="Wheat Flour 10kg", sku="FLOUR-10", is_active=True)
    product_repo = InMemoryProductRepository([product])
    stock_repo = InMemoryStockRepository()

    movements = [
        _create_mock_movement("prod-http-1", 70.0, days_ago=25),
        _create_mock_movement("prod-http-1", 70.0, days_ago=18),
        _create_mock_movement("prod-http-1", 70.0, days_ago=11),
        _create_mock_movement("prod-http-1", 70.0, days_ago=3),
    ]
    forecast_repo = InMemoryForecastRepository(
        initial_movements=movements,
        initial_products=[
            {
                "id": "prod-http-1",
                "name": "Wheat Flour 10kg",
                "sku": "FLOUR-10",
                "category": "Flour",
            }
        ],
    )

    service = ForecastingService(
        forecast_repo=forecast_repo,
        stock_repo=stock_repo,
        product_repo=product_repo,
        strategies=[MovingAverageForecast(), ExponentialSmoothingForecast()],
        default_strategy="moving_average",
    )

    app = create_app()
    app.dependency_overrides[get_forecasting_service] = lambda: service
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id="usr-test",
        email="owner@wareflow.local",
        role="owner",
        permissions={"inventory:view", "inventory:manage"},
    )

    client = TestClient(app)

    # 1. Product forecast endpoint
    resp_single = client.get("/products/prod-http-1/forecast?horizon_days=30")
    assert resp_single.status_code == 200
    data_single = resp_single.json()
    assert data_single["product_id"] == "prod-http-1"
    assert data_single["strategy"] == "moving_average"
    assert data_single["predicted_daily_demand"] == 10.0
    assert data_single["total_predicted_demand"] == 300.0

    # 2. Product forecast with strategy override
    resp_override = client.get("/products/prod-http-1/forecast?strategy=exponential_smoothing")
    assert resp_override.status_code == 200
    data_override = resp_override.json()
    assert data_override["strategy"] == "exponential_smoothing"

    # 3. Analytics forecast summary endpoint
    resp_summary = client.get("/analytics/forecast-summary?horizon_days=30")
    assert resp_summary.status_code == 200
    data_summary = resp_summary.json()
    assert data_summary["total_products_analyzed"] == 1
    assert len(data_summary["top_movers"]) == 1
    assert data_summary["top_movers"][0]["product_id"] == "prod-http-1"
