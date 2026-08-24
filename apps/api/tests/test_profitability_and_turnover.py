"""
Unit and Integration Tests for Profitability & Inventory Turnover Analytics (Step 16.1).

Verifies:
1. Gross margin calculations match hand-computed checks for products across multiple pricing tiers.
2. Grouping by product, category, and retailer rollups match arithmetic sums.
3. Turnover ratio and days of stock on hand correctly differentiate fast, slowing, and at-risk products.
4. HTTP API endpoints GET /analytics/profitability and GET /analytics/turnover return 200 with typed responses.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.core.di import get_profitability_service, get_turnover_service
from app.core.security import get_current_user
from app.main import create_app
from app.models.catalog import Category, Product
from app.models.retailer import BuyerTypeEnum, Retailer, SalesOrder, SalesOrderItem, SOStatusEnum
from app.schemas.analytics import ProfitabilityResponse, TurnoverResponse
from app.services.profitability_service import ProfitabilityService
from app.services.turnover_service import TurnoverService


# --- Fixtures ---


@pytest.fixture
def mock_catalog_and_orders():
    """Mock product catalog, categories, retailers, stock, and sales orders."""
    # Categories
    cat_grains = Category(id="cat-grains", name="Grains & Rice")
    cat_oils = Category(id="cat-oils", name="Edible Oils")

    # Products
    # Product 1: Royal Basmati Rice (Cost: ₹400, Wholesale: ₹500)
    p1 = Product(
        id="prod-1",
        name="Royal Basmati Rice 5kg",
        sku="RIC-BAS-001",
        cost_price=400.0,
        wholesale_price=500.0,
        category_id="cat-grains",
        category=cat_grains,
        unit="Bag",
        is_active=True,
    )
    # Product 2: Sona Masoori Rice (Cost: ₹300, Wholesale: ₹380)
    p2 = Product(
        id="prod-2",
        name="Sona Masoori Rice 5kg",
        sku="RIC-SON-002",
        cost_price=300.0,
        wholesale_price=380.0,
        category_id="cat-grains",
        category=cat_grains,
        unit="Bag",
        is_active=True,
    )
    # Product 3: Fortune Sunflower Oil 1L (Cost: ₹120, Wholesale: ₹150)
    p3 = Product(
        id="prod-3",
        name="Fortune Sunflower Oil 1L",
        sku="OIL-SUN-003",
        cost_price=120.0,
        wholesale_price=150.0,
        category_id="cat-oils",
        category=cat_oils,
        unit="Pouch",
        is_active=True,
    )

    products = [p1, p2, p3]

    # Retailers
    # Retailer 1: Apex Supermarket (Gold Tier - discounted selling price e.g. ₹480 for P1, ₹140 for P3)
    r1 = Retailer(
        id="ret-apex",
        name="Apex Supermarket",
        pricing_tier="gold",
        is_active=True,
    )
    # Retailer 2: Bharat Kirana (Standard Tier - standard selling price e.g. ₹500 for P1, ₹380 for P2)
    r2 = Retailer(
        id="ret-bharat",
        name="Bharat Kirana",
        pricing_tier="standard",
        is_active=True,
    )

    retailers = [r1, r2]

    # Orders in period
    # Order 1 (Apex - Gold): 10 x P1 @ ₹480 (Cost: 10 x 400 = 4000, Rev: 4800, Margin: 800)
    #                         20 x P3 @ ₹140 (Cost: 20 x 120 = 2400, Rev: 2800, Margin: 400)
    item1_1 = SalesOrderItem(id="item-1-1", product_id="prod-1", qty=10.0, unit_price=480.0, product=p1)
    item1_2 = SalesOrderItem(id="item-1-2", product_id="prod-3", qty=20.0, unit_price=140.0, product=p3)
    so1 = SalesOrder(
        id="so-1",
        so_number="SO-2026-0001",
        retailer_id="ret-apex",
        buyer_type=BuyerTypeEnum.RETAILER,
        status=SOStatusEnum.CONFIRMED,
        order_date=datetime.now(timezone.utc),
        items=[item1_1, item1_2],
        retailer=r1,
    )

    # Order 2 (Bharat - Standard): 5 x P1 @ ₹500 (Cost: 5 x 400 = 2000, Rev: 2500, Margin: 500)
    #                              15 x P2 @ ₹380 (Cost: 15 x 300 = 4500, Rev: 5700, Margin: 1200)
    item2_1 = SalesOrderItem(id="item-2-1", product_id="prod-1", qty=5.0, unit_price=500.0, product=p1)
    item2_2 = SalesOrderItem(id="item-2-2", product_id="prod-2", qty=15.0, unit_price=380.0, product=p2)
    so2 = SalesOrder(
        id="so-2",
        so_number="SO-2026-0002",
        retailer_id="ret-bharat",
        buyer_type=BuyerTypeEnum.RETAILER,
        status=SOStatusEnum.DELIVERED,
        order_date=datetime.now(timezone.utc),
        items=[item2_1, item2_2],
        retailer=r2,
    )

    orders = [so1, so2]

    # Stock on hand map
    # P1 (Fast): on_hand = 15, units_sold = 15 -> avg_on_hand = 15 + 7.5 = 22.5, turnover = 15 / 22.5 = 0.67 (or with 10 on hand -> 15 / 17.5 = 0.86)
    # P3 (Fastest): on_hand = 5, units_sold = 20 -> avg_on_hand = 5 + 10 = 15, turnover = 20 / 15 = 1.33 (healthy >= 1.0)
    # P2 (Moderate/Slowing): on_hand = 60, units_sold = 15 -> avg_on_hand = 60 + 7.5 = 67.5, turnover = 15 / 67.5 = 0.22 (at-risk < 0.3)
    stock_on_hand = {
        "prod-1": 15.0,
        "prod-2": 60.0,
        "prod-3": 5.0,
    }

    return {
        "products": products,
        "retailers": retailers,
        "orders": orders,
        "stock_on_hand": stock_on_hand,
    }


# --- Unit Tests: Profitability ---


def test_profitability_by_product_hand_computed_check(mock_catalog_and_orders):
    """
    QA Checklist item: Verify gross margin calculations for 3 products across 2 retailer tiers.

    Hand-computed truth:
    - P1 (Royal Basmati):
        Sales: 10 @ 480 + 5 @ 500 = 7300 Revenue, 15 units sold
        Cost: 15 @ 400 = 6000 Cost
        Gross Margin INR: 7300 - 6000 = 1300
        Gross Margin %: 1300 / 7300 * 100 = 17.8%
    - P2 (Sona Masoori):
        Sales: 15 @ 380 = 5700 Revenue, 15 units sold
        Cost: 15 @ 300 = 4500 Cost
        Gross Margin INR: 5700 - 4500 = 1200
        Gross Margin %: 1200 / 5700 * 100 = 21.1%
    - P3 (Sunflower Oil):
        Sales: 20 @ 140 = 2800 Revenue, 20 units sold
        Cost: 20 @ 120 = 2400 Cost
        Gross Margin INR: 2800 - 2400 = 400
        Gross Margin %: 400 / 2800 * 100 = 14.3%

    Summary:
        Total Revenue = 7300 + 5700 + 2800 = 15800
        Total Cost = 6000 + 4500 + 2400 = 12900
        Total Margin INR = 15800 - 12900 = 2900
        Overall Margin % = 2900 / 15800 * 100 = 18.4%
    """
    data = mock_catalog_and_orders

    mock_so_repo = MagicMock()
    mock_so_repo.list_all.return_value = (data["orders"], len(data["orders"]))

    mock_prod_repo = MagicMock()
    mock_prod_repo.list_products.return_value = data["products"]

    mock_ret_repo = MagicMock()
    mock_ret_repo.list_all.return_value = data["retailers"]

    service = ProfitabilityService(
        sales_order_repo=mock_so_repo,
        product_repo=mock_prod_repo,
        retailer_repo=mock_ret_repo,
    )

    res = service.get_profitability(group_by="product", period="30d")

    assert res.summary.total_revenue == 15800.0
    assert res.summary.total_cost == 12900.0
    assert res.summary.total_gross_margin_inr == 2900.0
    assert res.summary.overall_margin_pct == 18.4
    assert res.summary.total_units_sold == 50.0

    # Check P1
    p1_item = next(i for i in res.items if i.id == "prod-1")
    assert p1_item.units_sold == 15.0
    assert p1_item.total_revenue == 7300.0
    assert p1_item.total_cost == 6000.0
    assert p1_item.gross_margin_inr == 1300.0
    assert p1_item.gross_margin_pct == 17.8

    # Check P2
    p2_item = next(i for i in res.items if i.id == "prod-2")
    assert p2_item.units_sold == 15.0
    assert p2_item.total_revenue == 5700.0
    assert p2_item.total_cost == 4500.0
    assert p2_item.gross_margin_inr == 1200.0
    assert p2_item.gross_margin_pct == 21.1

    # Check P3
    p3_item = next(i for i in res.items if i.id == "prod-3")
    assert p3_item.units_sold == 20.0
    assert p3_item.total_revenue == 2800.0
    assert p3_item.total_cost == 2400.0
    assert p3_item.gross_margin_inr == 400.0
    assert p3_item.gross_margin_pct == 14.3


def test_profitability_by_category_rollup(mock_catalog_and_orders):
    """
    Verify grouping by Category aggregates correctly:
    - Grains & Rice: P1 + P2
        Revenue = 7300 + 5700 = 13000
        Cost = 6000 + 4500 = 10500
        Margin INR = 2500
        Margin % = 2500 / 13000 * 100 = 19.2%
    - Edible Oils: P3
        Revenue = 2800
        Cost = 2400
        Margin INR = 400
        Margin % = 14.3%
    """
    data = mock_catalog_and_orders

    mock_so_repo = MagicMock()
    mock_so_repo.list_all.return_value = (data["orders"], len(data["orders"]))
    mock_prod_repo = MagicMock()
    mock_prod_repo.list_products.return_value = data["products"]
    mock_ret_repo = MagicMock()
    mock_ret_repo.list_all.return_value = data["retailers"]

    service = ProfitabilityService(mock_so_repo, mock_prod_repo, mock_ret_repo)
    res = service.get_profitability(group_by="category", period="30d")

    assert res.summary.total_revenue == 15800.0
    assert len(res.items) == 2

    grains = next(i for i in res.items if i.id == "cat-grains")
    assert grains.name == "Grains & Rice"
    assert grains.total_revenue == 13000.0
    assert grains.total_cost == 10500.0
    assert grains.gross_margin_inr == 2500.0
    assert grains.gross_margin_pct == 19.2

    oils = next(i for i in res.items if i.id == "cat-oils")
    assert oils.name == "Edible Oils"
    assert oils.total_revenue == 2800.0
    assert oils.total_cost == 2400.0
    assert oils.gross_margin_inr == 400.0
    assert oils.gross_margin_pct == 14.3


def test_profitability_by_retailer_rollup(mock_catalog_and_orders):
    """
    Verify grouping by Retailer aggregates correctly:
    - Apex Supermarket (Gold Tier): SO-1
        Revenue = 4800 (P1) + 2800 (P3) = 7600
        Cost = 4000 + 2400 = 6400
        Margin INR = 1200
        Margin % = 1200 / 7600 * 100 = 15.8%
    - Bharat Kirana (Standard Tier): SO-2
        Revenue = 2500 (P1) + 5700 (P2) = 8200
        Cost = 2000 + 4500 = 6500
        Margin INR = 1700
        Margin % = 1700 / 8200 * 100 = 20.7%
    """
    data = mock_catalog_and_orders

    mock_so_repo = MagicMock()
    mock_so_repo.list_all.return_value = (data["orders"], len(data["orders"]))
    mock_prod_repo = MagicMock()
    mock_prod_repo.list_products.return_value = data["products"]
    mock_ret_repo = MagicMock()
    mock_ret_repo.list_all.return_value = data["retailers"]

    service = ProfitabilityService(mock_so_repo, mock_prod_repo, mock_ret_repo)
    res = service.get_profitability(group_by="retailer", period="30d")

    assert res.summary.total_revenue == 15800.0
    assert len(res.items) == 2

    apex = next(i for i in res.items if i.id == "ret-apex")
    assert apex.name == "Apex Supermarket"
    assert apex.badge == "GOLD"
    assert apex.total_revenue == 7600.0
    assert apex.total_cost == 6400.0
    assert apex.gross_margin_inr == 1200.0
    assert apex.gross_margin_pct == 15.8

    bharat = next(i for i in res.items if i.id == "ret-bharat")
    assert bharat.name == "Bharat Kirana"
    assert bharat.badge == "STANDARD"
    assert bharat.total_revenue == 8200.0
    assert bharat.total_cost == 6500.0
    assert bharat.gross_margin_inr == 1700.0
    assert bharat.gross_margin_pct == 20.7


# --- Unit Tests: Inventory Turnover ---


def test_turnover_ranking_and_banding(mock_catalog_and_orders):
    """
    QA Checklist item: Turnover ratio correctly reflects crafted scenario:
    - P3 (Oil): Units sold = 20, On-hand = 5 -> Avg Stock = 15 -> Turnover = 20 / 15 = 1.33 -> Healthy (>= 1.0)
    - P1 (Basmati): Units sold = 15, On-hand = 15 -> Avg Stock = 22.5 -> Turnover = 15 / 22.5 = 0.67 -> Slowing (0.3 <= ratio < 1.0)
    - P2 (Sona Masoori): Units sold = 15, On-hand = 60 -> Avg Stock = 67.5 -> Turnover = 15 / 67.5 = 0.22 -> At-Risk (< 0.3)

    Default ranking should sort slowest-to-fastest (P2 first, then P1, then P3).
    """
    data = mock_catalog_and_orders

    mock_so_repo = MagicMock()
    mock_so_repo.list_all.return_value = (data["orders"], len(data["orders"]))
    mock_prod_repo = MagicMock()
    mock_prod_repo.list_products.return_value = data["products"]

    mock_stock_repo = MagicMock()
    mock_stock_repo.get_on_hand.side_effect = lambda p_id: data["stock_on_hand"].get(p_id, 0.0)

    service = TurnoverService(
        sales_order_repo=mock_so_repo,
        product_repo=mock_prod_repo,
        stock_repo=mock_stock_repo,
    )

    res = service.get_turnover(period="30d")

    assert res.summary.total_products == 3
    assert res.summary.healthy_count == 1
    assert res.summary.slowing_count == 1
    assert res.summary.at_risk_count == 1

    # Verify slowest-to-fastest sort order
    assert res.items[0].product_id == "prod-2"
    assert res.items[0].turnover_ratio == 0.22
    assert res.items[0].turnover_band == "at_risk"
    assert res.items[0].days_of_stock == 135.0  # (67.5 / 15) * 30 = 135 days

    assert res.items[1].product_id == "prod-1"
    assert res.items[1].turnover_ratio == 0.67
    assert res.items[1].turnover_band == "slowing"
    assert res.items[1].days_of_stock == 45.0  # (22.5 / 15) * 30 = 45 days

    assert res.items[2].product_id == "prod-3"
    assert res.items[2].turnover_ratio == 1.33
    assert res.items[2].turnover_band == "healthy"
    assert res.items[2].days_of_stock == 22.5  # (15 / 20) * 30 = 22.5 days


# --- Integration Tests: FastAPI Endpoints ---


def test_api_profitability_endpoint(mock_catalog_and_orders):
    """Verify GET /analytics/profitability returns 200 and schema compliant JSON."""
    data = mock_catalog_and_orders

    mock_so_repo = MagicMock()
    mock_so_repo.list_all.return_value = (data["orders"], len(data["orders"]))
    mock_prod_repo = MagicMock()
    mock_prod_repo.list_products.return_value = data["products"]
    mock_ret_repo = MagicMock()
    mock_ret_repo.list_all.return_value = data["retailers"]

    profitability_service = ProfitabilityService(mock_so_repo, mock_prod_repo, mock_ret_repo)

    app = create_app()
    app.dependency_overrides[get_profitability_service] = lambda: profitability_service
    app.dependency_overrides[get_current_user] = lambda: MagicMock(
        id="u-1", email="owner@wareflow.com", role_name="Owner", permissions=["all"]
    )

    client = TestClient(app)
    response = client.get("/analytics/profitability?group_by=product&period=30d")
    assert response.status_code == 200

    payload = response.json()
    assert payload["group_by"] == "product"
    assert payload["summary"]["total_revenue"] == 15800.0
    assert len(payload["items"]) == 3


def test_api_turnover_endpoint(mock_catalog_and_orders):
    """Verify GET /analytics/turnover returns 200 and schema compliant JSON."""
    data = mock_catalog_and_orders

    mock_so_repo = MagicMock()
    mock_so_repo.list_all.return_value = (data["orders"], len(data["orders"]))
    mock_prod_repo = MagicMock()
    mock_prod_repo.list_products.return_value = data["products"]
    mock_stock_repo = MagicMock()
    mock_stock_repo.get_on_hand.side_effect = lambda p_id: data["stock_on_hand"].get(p_id, 0.0)

    turnover_service = TurnoverService(mock_so_repo, mock_prod_repo, mock_stock_repo)

    app = create_app()
    app.dependency_overrides[get_turnover_service] = lambda: turnover_service
    app.dependency_overrides[get_current_user] = lambda: MagicMock(
        id="u-1", email="owner@wareflow.com", role_name="Owner", permissions=["all"]
    )

    client = TestClient(app)
    response = client.get("/analytics/turnover?period=30d")
    assert response.status_code == 200

    payload = response.json()
    assert payload["period"] == "30d"
    assert payload["summary"]["total_products"] == 3
    assert payload["items"][0]["turnover_band"] == "at_risk"
