"""Unit and integration tests for Step 14.2 Reorder Suggestions & Dead-Stock Detection."""

import uuid
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.core.di import (
    get_dead_stock_service,
    get_forecasting_service,
    get_reorder_suggestion_service,
)
from app.core.security import CurrentUser, get_current_user
from app.main import create_app
from app.models.inventory import StockMovement, StockMovementTypeEnum
from app.repositories.impl.forecast_repository import InMemoryForecastRepository
from app.repositories.impl.product_repository import InMemoryProductRepository
from app.repositories.impl.purchase_order_repository import InMemoryPurchaseOrderRepository
from app.repositories.impl.stock_repository import InMemoryStockRepository
from app.repositories.impl.supplier_repository import InMemorySupplierRepository
from app.schemas.analytics import (
    CreatePOFromSuggestionsRequest,
    POFromSuggestionItem,
)
from app.services.dead_stock_service import DeadStockService
from app.services.forecasting.moving_average import MovingAverageForecast
from app.services.forecasting_service import ForecastingService
from app.services.purchase_order_service import PurchaseOrderService
from app.services.reorder_suggestion_service import ReorderSuggestionService
from app.services.stock_service import StockService


def create_mock_environment():
    """Create in-memory repos and wired services for testing."""
    product_repo = InMemoryProductRepository()
    stock_repo = InMemoryStockRepository()
    forecast_repo = InMemoryForecastRepository()
    supplier_repo = InMemorySupplierRepository()
    po_repo = InMemoryPurchaseOrderRepository()

    stock_service = StockService(stock_repo=stock_repo)
    po_service = PurchaseOrderService(
        po_repo=po_repo,
        supplier_repo=supplier_repo,
        product_repo=product_repo,
        stock_service=stock_service,
    )

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
        po_service=po_service,
    )

    dead_stock_service = DeadStockService(
        product_repo=product_repo,
        stock_repo=stock_repo,
        forecast_repo=forecast_repo,
    )

    return {
        "product_repo": product_repo,
        "stock_repo": stock_repo,
        "forecast_repo": forecast_repo,
        "supplier_repo": supplier_repo,
        "po_repo": po_repo,
        "po_service": po_service,
        "forecasting_service": forecasting_service,
        "reorder_service": reorder_service,
        "dead_stock_service": dead_stock_service,
    }


def add_stock_batch(stock_repo: InMemoryStockRepository, product_id: str, quantity: float, warehouse_id: str = "wh-1"):
    """Helper to add on-hand stock batch to InMemoryStockRepository."""
    bid = str(uuid.uuid4())
    stock_repo.batches[bid] = {
        "id": bid,
        "product_id": product_id,
        "warehouse_id": warehouse_id,
        "batch_no": f"BATCH-{bid[:8]}",
        "quantity": float(quantity),
        "expiry_date": None,
        "received_at": datetime.now(UTC),
    }


def test_reorder_suggestions_hand_computed_check():
    """Verify reorder suggestions against hand-computed benchmark for 2 low-stock products."""
    env = create_mock_environment()
    prod_repo = env["product_repo"]
    stock_repo = env["stock_repo"]
    forecast_repo = env["forecast_repo"]
    reorder_service = env["reorder_service"]

    now = datetime.now(UTC)

    # Product 1: Basmati Rice (on_hand = 5, reorder_point = 10, reorder_qty = 20, cost_price = 100)
    # Sales history: 4 weeks of 14 units/week (2 units/day).
    prod_repo.create_product(
        {
            "id": "prod-rice-1",
            "name": "Basmati Rice 5kg",
            "sku": "RICE-001",
            "cost_price": 100.0,
            "wholesale_price": 120.0,
            "reorder_point": 10,
            "reorder_qty": 20,
            "unit": "Bag",
            "is_active": True,
        }
    )
    # On-hand = 5
    add_stock_batch(stock_repo, "prod-rice-1", 5.0)

    # 4 weeks of outbound movements: 14 per week -> 2.0 daily demand
    for i in range(4):
        m = StockMovement(
            id=str(uuid.uuid4()),
            product_id="prod-rice-1",
            warehouse_id="wh-1",
            type=StockMovementTypeEnum.OUT,
            quantity=14.0,
            created_at=now - timedelta(days=25 - (i * 7)),
        )
        forecast_repo.save_movement(m)

    # Product 2: Mustard Oil (on_hand = 8, reorder_point = 15, reorder_qty = 50, cost_price = 200)
    # Sales history: 4 weeks of 7 units/week (1 unit/day).
    prod_repo.create_product(
        {
            "id": "prod-oil-2",
            "name": "Mustard Oil 1L",
            "sku": "OIL-002",
            "cost_price": 200.0,
            "wholesale_price": 230.0,
            "reorder_point": 15,
            "reorder_qty": 50,
            "unit": "Bottle",
            "is_active": True,
        }
    )
    # On-hand = 8
    add_stock_batch(stock_repo, "prod-oil-2", 8.0)

    for i in range(4):
        m = StockMovement(
            id=str(uuid.uuid4()),
            product_id="prod-oil-2",
            warehouse_id="wh-1",
            type=StockMovementTypeEnum.OUT,
            quantity=7.0,
            created_at=now - timedelta(days=25 - (i * 7)),
        )
        forecast_repo.save_movement(m)

    # Product 3: High Stock Product (on_hand = 100, reorder_point = 10) -> Should NOT appear in suggestions
    prod_repo.create_product(
        {
            "id": "prod-sugar-3",
            "name": "Sugar 1kg",
            "sku": "SUGAR-003",
            "cost_price": 40.0,
            "wholesale_price": 50.0,
            "reorder_point": 10,
            "reorder_qty": 30,
            "unit": "Bag",
            "is_active": True,
        }
    )
    # On-hand = 100
    add_stock_batch(stock_repo, "prod-sugar-3", 100.0)

    # Run reorder suggestions with lead_time_buffer_days = 14
    suggestions = reorder_service.get_reorder_suggestions(lead_time_buffer_days=14)

    # Verify count: exactly prod1 and prod2
    assert suggestions.total_suggested_items == 2
    assert {item.product_id for item in suggestions.items} == {"prod-rice-1", "prod-oil-2"}

    # Hand-computed check on Product 1:
    # daily_demand = 2.0. lead_time_demand = ceil(2.0 * 14) = 28.
    # suggested_qty = max(20, 28) = 28.
    # unit_cost = 100.0, estimated_cost = 28 * 100 = 2800.0.
    # on_hand = 5, days_remaining = 5 / 2.0 = 2.5 days (<= 3.0 -> urgency = "critical").
    item_rice = next(i for i in suggestions.items if i.product_id == "prod-rice-1")
    assert item_rice.forecasted_daily_demand == 2.0
    assert item_rice.suggested_reorder_qty == 28
    assert item_rice.estimated_cost == 2800.0
    assert item_rice.days_of_stock_remaining == 2.5
    assert item_rice.urgency == "critical"

    # Hand-computed check on Product 2:
    # daily_demand = 1.0. lead_time_demand = ceil(1.0 * 14) = 14.
    # suggested_qty = max(50, 14) = 50.
    # unit_cost = 200.0, estimated_cost = 50 * 200 = 10000.0.
    # on_hand = 8, days_remaining = 8 / 1.0 = 8.0 days.
    item_oil = next(i for i in suggestions.items if i.product_id == "prod-oil-2")
    assert item_oil.forecasted_daily_demand == 1.0
    assert item_oil.suggested_reorder_qty == 50
    assert item_oil.estimated_cost == 10000.0
    assert item_oil.days_of_stock_remaining == 8.0

    # Total estimated cost check: 2800 + 10000 = 12800.0
    assert suggestions.total_estimated_cost == 12800.0


def test_create_po_from_suggestions_produces_prefilled_draft_po():
    """Verify 'Create PO from suggestions' produces a correctly pre-filled draft Purchase Order."""
    env = create_mock_environment()
    prod_repo = env["product_repo"]
    supplier_repo = env["supplier_repo"]
    reorder_service = env["reorder_service"]
    po_repo = env["po_repo"]

    # Setup supplier
    supplier_repo.create_supplier(
        {
            "id": "sup-agro-1",
            "name": "Agro Commodities Ltd",
            "email": "orders@agro.com",
            "phone": "+919876543210",
            "is_active": True,
        }
    )

    # Setup product
    prod_repo.create_product(
        {
            "id": "prod-wheat-1",
            "name": "Premium Wheat 10kg",
            "sku": "WHEAT-001",
            "cost_price": 250.0,
            "wholesale_price": 290.0,
            "reorder_point": 20,
            "reorder_qty": 40,
            "unit": "Bag",
            "is_active": True,
        }
    )

    req = CreatePOFromSuggestionsRequest(
        supplier_id="sup-agro-1",
        items=[
            POFromSuggestionItem(
                product_id="prod-wheat-1",
                qty_ordered=40.0,
                unit_cost=250.0,
            )
        ],
        expected_date="2026-09-01",
        notes="Automated PO from AI Reorder Suggestions",
    )

    created_po = reorder_service.create_po_from_suggestions(
        request=req,
        created_by_name="admin@wareflow.local",
    )

    # Verify PO attributes
    assert created_po.id is not None
    assert created_po.po_number.startswith("PO-")
    assert created_po.supplier_id == "sup-agro-1"
    assert created_po.supplier_name == "Agro Commodities Ltd"
    assert created_po.status == "draft"
    assert created_po.total_amount == 10000.0  # 40 * 250
    assert len(created_po.items) == 1
    assert created_po.items[0].product_id == "prod-wheat-1"
    assert created_po.items[0].qty_ordered == 40.0
    assert created_po.items[0].unit_cost == 250.0

    # Verify persisted in PO repository
    persisted = po_repo.get_by_id(created_po.id)
    assert persisted is not None
    assert persisted.supplier_id == "sup-agro-1"


def test_dead_stock_detection_and_window_exclusion():
    """Verify dead stock detection excludes products with recent sales and ranks by tied-up capital."""
    env = create_mock_environment()
    prod_repo = env["product_repo"]
    stock_repo = env["stock_repo"]
    forecast_repo = env["forecast_repo"]
    dead_stock_service = env["dead_stock_service"]

    now = datetime.now(UTC)

    # 1. Product A (Active Seller): on_hand = 20, cost = 50. Outbound sale 20 days ago.
    # Should be EXCLUDED from dead-stock in a 90-day window.
    prod_repo.create_product(
        {
            "id": "prod-a",
            "name": "Active Tea 250g",
            "sku": "TEA-01",
            "cost_price": 50.0,
            "wholesale_price": 65.0,
            "is_active": True,
        }
    )
    add_stock_batch(stock_repo, "prod-a", 20.0)
    forecast_repo.save_movement(
        StockMovement(
            id=str(uuid.uuid4()),
            product_id="prod-a",
            warehouse_id="wh-1",
            type=StockMovementTypeEnum.OUT,
            quantity=5.0,
            created_at=now - timedelta(days=20),
        )
    )

    # 2. Product B (Dead Stock 1): on_hand = 40, cost = 100 -> Tied-up Capital = 4000. No sales at all.
    prod_repo.create_product(
        {
            "id": "prod-b",
            "name": "Dead Coffee Beans 1kg",
            "sku": "COFFEE-01",
            "cost_price": 100.0,
            "wholesale_price": 140.0,
            "is_active": True,
            "created_at": now - timedelta(days=120),
        }
    )
    add_stock_batch(stock_repo, "prod-b", 40.0)

    # 3. Product C (Dead Stock 2): on_hand = 10, cost = 300 -> Tied-up Capital = 3000. Last sale 100 days ago.
    prod_repo.create_product(
        {
            "id": "prod-c",
            "name": "Slow Almond Oil 500ml",
            "sku": "ALMOND-01",
            "cost_price": 300.0,
            "wholesale_price": 380.0,
            "is_active": True,
        }
    )
    add_stock_batch(stock_repo, "prod-c", 10.0)
    forecast_repo.save_movement(
        StockMovement(
            id=str(uuid.uuid4()),
            product_id="prod-c",
            warehouse_id="wh-1",
            type=StockMovementTypeEnum.OUT,
            quantity=2.0,
            created_at=now - timedelta(days=100),
        )
    )

    # 4. Product D (Zero stock, no sales): on_hand = 0.
    # Should be EXCLUDED because there are 0 units tying up capital.
    prod_repo.create_product(
        {
            "id": "prod-d",
            "name": "Out of Stock Spice",
            "sku": "SPICE-01",
            "cost_price": 20.0,
            "wholesale_price": 30.0,
            "is_active": True,
        }
    )

    # Test 90-day window:
    dead_90 = dead_stock_service.get_dead_stock(window_days=90)
    assert dead_90.total_dead_items == 2
    # Check that Active Product A and Out-of-stock Product D are excluded
    dead_ids = [item.product_id for item in dead_90.items]
    assert dead_ids == ["prod-b", "prod-c"]  # prod-b (4000) ranked before prod-c (3000)

    assert dead_90.items[0].tied_up_capital == 4000.0
    assert dead_90.items[1].tied_up_capital == 3000.0
    assert dead_90.total_tied_up_capital == 7000.0

    # Test 120-day window: Product C had a sale at day 100, so in a 120-day window it has a sale
    # Therefore in a 120-day window, Product C is NOT dead stock!
    dead_120 = dead_stock_service.get_dead_stock(window_days=120)
    assert dead_120.total_dead_items == 1
    assert dead_120.items[0].product_id == "prod-b"


def test_api_reorder_and_dead_stock_endpoints():
    """Verify HTTP API endpoints for /analytics/reorder-suggestions and /analytics/dead-stock."""
    app = create_app()
    env = create_mock_environment()

    app.dependency_overrides[get_reorder_suggestion_service] = lambda: env["reorder_service"]
    app.dependency_overrides[get_dead_stock_service] = lambda: env["dead_stock_service"]
    app.dependency_overrides[get_forecasting_service] = lambda: env["forecasting_service"]
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id="user-1",
        email="test@wareflow.local",
        role="admin",
        permissions=["inventory:view", "inventory:create"],
    )

    client = TestClient(app)

    # Seed 1 low stock product and 1 supplier
    env["supplier_repo"].create_supplier(
        {
            "id": "sup-test-1",
            "name": "Apex Agro Ltd",
            "is_active": True,
        }
    )
    env["product_repo"].create_product(
        {
            "id": "prod-api-1",
            "name": "Organic Lentils 1kg",
            "sku": "LENTIL-01",
            "cost_price": 80.0,
            "reorder_point": 25,
            "reorder_qty": 60,
            "is_active": True,
        }
    )
    add_stock_batch(env["stock_repo"], "prod-api-1", 10.0)

    # 1. GET /analytics/reorder-suggestions
    res_reorder = client.get("/analytics/reorder-suggestions")
    assert res_reorder.status_code == 200
    data = res_reorder.json()
    assert "items" in data
    assert data["total_suggested_items"] >= 1
    assert data["items"][0]["product_id"] == "prod-api-1"
    assert data["items"][0]["suggested_reorder_qty"] == 60

    # 2. POST /analytics/reorder-suggestions/create-po
    po_payload = {
        "supplier_id": "sup-test-1",
        "items": [
            {
                "product_id": "prod-api-1",
                "qty_ordered": 60,
                "unit_cost": 80.0,
            }
        ],
        "expected_date": "2026-09-15",
        "notes": "Fast reorder",
    }
    res_create_po = client.post("/analytics/reorder-suggestions/create-po", json=po_payload)
    assert res_create_po.status_code == 201
    po_data = res_create_po.json()
    assert po_data["supplier_id"] == "sup-test-1"
    assert po_data["total_amount"] == 4800.0

    # 3. GET /analytics/dead-stock
    res_dead = client.get("/analytics/dead-stock?window_days=60")
    assert res_dead.status_code == 200
    dead_data = res_dead.json()
    assert "items" in dead_data
    assert "total_tied_up_capital" in dead_data
    assert dead_data["window_days"] == 60
