"""Automated unit and integration tests for Stock Analytics & Composition Dashboard (Step 6.1)."""

from datetime import date, datetime, timedelta

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.api.routers import stock_analytics as stock_analytics_router
from app.core.security import CurrentUser, get_current_user
from app.db.base import Base
from app.models.catalog import Category, Product
from app.models.supplier import POStatusEnum, PurchaseOrder, PurchaseOrderItem, Supplier
from app.models.uom import UnitOfMeasure
from app.models.warehouse import StockBatch, Warehouse
from app.repositories.impl.stock_analytics_repository import (
    InMemoryStockAnalyticsRepository,
    SqlAlchemyStockAnalyticsRepository,
)
from app.services.stock_analytics_service import StockAnalyticsService


@pytest.fixture
def analytics_db():
    """Create in-memory SQLite database for Analytics testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mock_user() -> CurrentUser:
    return CurrentUser(
        id="analytics-officer-1",
        email="analytics@wareflow.io",
        role="Manager",
        permissions={"inventory:view"},
    )


def test_analytics_dip_in_memory_repository():
    """DIP Verification: Test StockAnalyticsService with InMemoryStockAnalyticsRepository."""
    products = [
        {"id": "p1", "sku": "P1", "name": "Item 1", "cost_price": 50.0, "category_id": "c1", "is_active": True, "reorder_point": 100},
        {"id": "p2", "sku": "P2", "name": "Item 2", "cost_price": 20.0, "category_id": "c2", "is_active": True, "reorder_point": 50},
    ]
    categories = [
        {"id": "c1", "name": "Grains"},
        {"id": "c2", "name": "Oils"},
    ]
    warehouses = [
        {"id": "w1", "name": "Central Hub"},
    ]
    batches = [
        {"id": "b1", "product_id": "p1", "warehouse_id": "w1", "quantity": 10.0, "batch_no": "B1"},  # 10 * 50 = 500
        {"id": "b2", "product_id": "p2", "warehouse_id": "w1", "quantity": 5.0, "batch_no": "B2"},   # 5 * 20 = 100
    ]

    repo = InMemoryStockAnalyticsRepository(
        products=products,
        categories=categories,
        warehouses=warehouses,
        batches=batches,
    )
    service = StockAnalyticsService(analytics_repo=repo)

    summary = service.get_value_summary()
    assert summary.total_stock_value == 600.0
    assert summary.total_units == 15.0
    assert len(summary.by_category) == 2
    assert summary.by_category[0].category_name == "Grains"
    assert summary.by_category[0].total_value == 500.0
    assert summary.by_category[0].percentage == 83.3


def test_hand_calculated_stock_value_summary_sql_parity(analytics_db):
    """
    QA Checklist item:
    Hand-calculated check against DB:
    Product 1 (cost 100) has 30 in WH1, 20 in WH2 -> Value = 5000
    Product 2 (cost 50) has 10 in WH1, 0 in WH2 -> Value = 500
    Total Value = 5500, Total Units = 60
    """
    cat_grain = Category(name="Grains & Pulses")
    cat_dairy = Category(name="Dairy & Cold")
    analytics_db.add_all([cat_grain, cat_dairy])
    analytics_db.commit()

    wh1 = Warehouse(name="North Central Hub", is_active=True)
    wh2 = Warehouse(name="South Coast Hub", is_active=True)
    analytics_db.add_all([wh1, wh2])
    analytics_db.commit()

    p1 = Product(sku="BASMATI", name="Basmati Rice", category_id=cat_grain.id, cost_price=100.0, wholesale_price=140.0, reorder_point=40)
    p2 = Product(sku="BUTTER", name="Cultured Butter", category_id=cat_dairy.id, cost_price=50.0, wholesale_price=70.0, reorder_point=20)
    analytics_db.add_all([p1, p2])
    analytics_db.commit()

    b1_1 = StockBatch(product_id=p1.id, warehouse_id=wh1.id, batch_no="B1", quantity=30.0)
    b1_2 = StockBatch(product_id=p1.id, warehouse_id=wh2.id, batch_no="B2", quantity=20.0)
    b2_1 = StockBatch(product_id=p2.id, warehouse_id=wh1.id, batch_no="B3", quantity=10.0)
    analytics_db.add_all([b1_1, b1_2, b2_1])
    analytics_db.commit()

    repo = SqlAlchemyStockAnalyticsRepository(session=analytics_db)
    service = StockAnalyticsService(analytics_repo=repo)

    summary = service.get_value_summary()
    assert summary.total_stock_value == 5500.0
    assert summary.total_units == 60.0
    assert summary.total_products == 2

    # Category checks
    grain_cat = next(c for c in summary.by_category if c.category_name == "Grains & Pulses")
    dairy_cat = next(c for c in summary.by_category if c.category_name == "Dairy & Cold")
    assert grain_cat.total_value == 5000.0
    assert grain_cat.total_units == 50.0
    assert grain_cat.percentage == 90.9
    assert dairy_cat.total_value == 500.0
    assert dairy_cat.total_units == 10.0
    assert dairy_cat.percentage == 9.1

    # Warehouse checks
    wh1_val = next(w for w in summary.by_warehouse if w.warehouse_name == "North Central Hub")
    wh2_val = next(w for w in summary.by_warehouse if w.warehouse_name == "South Coast Hub")
    # WH1: (30 * 100) + (10 * 50) = 3500
    assert wh1_val.total_value == 3500.0
    assert wh1_val.total_units == 40.0
    # WH2: 20 * 100 = 2000
    assert wh2_val.total_value == 2000.0
    assert wh2_val.total_units == 20.0


def test_health_distribution_and_critical_reclassification(analytics_db):
    """
    QA Checklist item:
    A product crossing into 'critical' stock status immediately reflects in the health-distribution chart.
    """
    p_healthy = Product(sku="H1", name="Healthy Item", cost_price=10, reorder_point=100)
    p_low = Product(sku="L1", name="Low Item", cost_price=10, reorder_point=100)
    p_crit = Product(sku="C1", name="Critical Item", cost_price=10, reorder_point=100)
    p_out = Product(sku="O1", name="Out of Stock Item", cost_price=10, reorder_point=100)
    analytics_db.add_all([p_healthy, p_low, p_crit, p_out])
    analytics_db.commit()

    wh = Warehouse(name="Main", is_active=True)
    analytics_db.add(wh)
    analytics_db.commit()

    # Healthy: 120 > 100
    b_h = StockBatch(product_id=p_healthy.id, warehouse_id=wh.id, batch_no="BH", quantity=120.0)
    # Low: 50 <= 100 and > 25
    b_l = StockBatch(product_id=p_low.id, warehouse_id=wh.id, batch_no="BL", quantity=50.0)
    # Critical: 15 <= 25
    b_c = StockBatch(product_id=p_crit.id, warehouse_id=wh.id, batch_no="BC", quantity=15.0)
    # Out: 0 quantity
    analytics_db.add_all([b_h, b_l, b_c])
    analytics_db.commit()

    repo = SqlAlchemyStockAnalyticsRepository(session=analytics_db)
    service = StockAnalyticsService(analytics_repo=repo)

    dist = service.get_health_distribution()
    assert dist.healthy_count == 1
    assert dist.low_count == 1
    assert dist.critical_count == 1
    assert dist.out_of_stock_count == 1
    assert dist.total_products == 4

    # Now simulate product healthy crossing into critical (reduce batch qty from 120 to 10)
    b_h.quantity = 10.0
    analytics_db.commit()

    updated_dist = service.get_health_distribution()
    assert updated_dist.healthy_count == 0
    assert updated_dist.critical_count == 2


def test_top_value_products_sorting(analytics_db):
    """Verify top products returned sorted by value and quantity."""
    uom = UnitOfMeasure(name="Kilogram", abbreviation="kg")
    analytics_db.add(uom)
    analytics_db.commit()

    p_expensive = Product(sku="EXP-1", name="Saffron 1kg", base_uom_id=uom.id, cost_price=1000.0, reorder_point=5)
    p_bulk = Product(sku="BULK-1", name="Coarse Salt 50kg", base_uom_id=uom.id, cost_price=5.0, reorder_point=100)
    analytics_db.add_all([p_expensive, p_bulk])
    analytics_db.commit()

    wh = Warehouse(name="Main Hub", is_active=True)
    analytics_db.add(wh)
    analytics_db.commit()

    b1 = StockBatch(product_id=p_expensive.id, warehouse_id=wh.id, batch_no="SF1", quantity=10.0)  # 10,000 value, 10 qty
    b2 = StockBatch(product_id=p_bulk.id, warehouse_id=wh.id, batch_no="SL1", quantity=500.0)       # 2,500 value, 500 qty
    analytics_db.add_all([b1, b2])
    analytics_db.commit()

    repo = SqlAlchemyStockAnalyticsRepository(session=analytics_db)
    service = StockAnalyticsService(analytics_repo=repo)

    top = service.get_top_products(limit=5)
    # Highest value: Saffron (10,000)
    assert top.by_value[0].sku == "EXP-1"
    assert top.by_value[0].total_value == 10000.0
    # Highest volume: Coarse Salt (500)
    assert top.by_quantity[0].sku == "BULK-1"
    assert top.by_quantity[0].total_on_hand == 500.0


def test_expiry_timeline_windows(analytics_db):
    """Verify expiry timeline groups batches into 6 window bins accurately."""
    wh = Warehouse(name="Cold Store", is_active=True)
    analytics_db.add(wh)
    analytics_db.commit()

    prod = Product(sku="DAIRY-1", name="Fresh Milk 1L", cost_price=20.0)
    analytics_db.add(prod)
    analytics_db.commit()

    today = date.today()
    # 1. Expired (5 days ago)
    b_exp = StockBatch(product_id=prod.id, warehouse_id=wh.id, batch_no="B-EXP", quantity=10.0, expiry_date=today - timedelta(days=5))
    # 2. This week (+4 days)
    b_wk = StockBatch(product_id=prod.id, warehouse_id=wh.id, batch_no="B-WK", quantity=20.0, expiry_date=today + timedelta(days=4))
    # 3. This month (+20 days)
    b_mo = StockBatch(product_id=prod.id, warehouse_id=wh.id, batch_no="B-MO", quantity=30.0, expiry_date=today + timedelta(days=20))
    # 4. Next 3 months (+60 days)
    b_3mo = StockBatch(product_id=prod.id, warehouse_id=wh.id, batch_no="B-3MO", quantity=40.0, expiry_date=today + timedelta(days=60))
    # 5. Later (+120 days)
    b_late = StockBatch(product_id=prod.id, warehouse_id=wh.id, batch_no="B-LATE", quantity=50.0, expiry_date=today + timedelta(days=120))
    # 6. No expiry
    b_none = StockBatch(product_id=prod.id, warehouse_id=wh.id, batch_no="B-NONE", quantity=60.0, expiry_date=None)

    analytics_db.add_all([b_exp, b_wk, b_mo, b_3mo, b_late, b_none])
    analytics_db.commit()

    repo = SqlAlchemyStockAnalyticsRepository(session=analytics_db)
    service = StockAnalyticsService(analytics_repo=repo)

    timeline = service.get_expiry_timeline()
    assert len(timeline.windows) == 6
    w_map = {w.window_key: w for w in timeline.windows}

    assert w_map["expired"].batch_count == 1
    assert w_map["expired"].total_quantity == 10.0
    assert w_map["this_week"].batch_count == 1
    assert w_map["this_week"].total_quantity == 20.0
    assert w_map["this_month"].batch_count == 1
    assert w_map["this_month"].total_quantity == 30.0
    assert w_map["next_3_months"].batch_count == 1
    assert w_map["next_3_months"].total_quantity == 40.0
    assert w_map["later"].batch_count == 1
    assert w_map["later"].total_quantity == 50.0
    assert w_map["no_expiry"].batch_count == 1
    assert w_map["no_expiry"].total_quantity == 60.0

    # Expiring soon = expired (10) + this_week (20) + this_month (30) = 60 units (3 batches)
    assert timeline.total_expiring_soon_count == 3
    assert timeline.total_expiring_soon_value == (10 + 20 + 30) * 20.0


def test_stock_analytics_rest_endpoints(analytics_db, mock_user):
    """Integration test verifying all 4 FastAPI stock analytics endpoints."""
    test_app = FastAPI()
    test_app.include_router(stock_analytics_router.router)

    def override_get_current_user():
        return mock_user

    def override_get_service():
        repo = SqlAlchemyStockAnalyticsRepository(session=analytics_db)
        return StockAnalyticsService(analytics_repo=repo)

    test_app.dependency_overrides[get_current_user] = override_get_current_user
    test_app.dependency_overrides[stock_analytics_router.get_stock_analytics_service] = override_get_service

    client = TestClient(test_app)

    wh = Warehouse(name="Central Depot", is_active=True)
    cat = Category(name="Beverages")
    analytics_db.add_all([wh, cat])
    analytics_db.commit()

    prod = Product(sku="BEV-TEA", name="Assam Black Tea", category_id=cat.id, cost_price=80.0, reorder_point=50)
    analytics_db.add(prod)
    analytics_db.commit()

    batch = StockBatch(product_id=prod.id, warehouse_id=wh.id, batch_no="TEA-B1", quantity=100.0, expiry_date=date.today() + timedelta(days=45))
    analytics_db.add(batch)
    analytics_db.commit()

    # 1. GET /analytics/stock/value-summary
    res1 = client.get("/analytics/stock/value-summary")
    assert res1.status_code == status.HTTP_200_OK
    assert res1.json()["total_stock_value"] == 8000.0
    assert len(res1.json()["by_category"]) == 1

    # 2. GET /analytics/stock/health-distribution
    res2 = client.get("/analytics/stock/health-distribution")
    assert res2.status_code == status.HTTP_200_OK
    assert res2.json()["healthy_count"] == 1

    # 3. GET /analytics/stock/top-value-products
    res3 = client.get("/analytics/stock/top-value-products?limit=5")
    assert res3.status_code == status.HTTP_200_OK
    assert len(res3.json()["by_value"]) == 1
    assert res3.json()["by_value"][0]["sku"] == "BEV-TEA"

    # 4. GET /analytics/stock/expiry-timeline
    res4 = client.get("/analytics/stock/expiry-timeline")
    assert res4.status_code == status.HTTP_200_OK
    assert len(res4.json()["windows"]) == 6


# --- Step 6.2: Purchasing Spend Analytics Tests ---


def test_spend_analytics_empty_pre_phase6(analytics_db):
    """
    QA Checklist item:
    With no purchase order data yet (current state, pre-Phase 6), every spend endpoint
    shows its clean empty structure — no NaN, no division-by-zero, no 500 error.
    """
    repo = SqlAlchemyStockAnalyticsRepository(session=analytics_db)
    service = StockAnalyticsService(analytics_repo=repo)

    # 1. Spend Trend
    trend = service.get_spend_trend(months=12)
    assert trend.total_period_spend == 0.0
    assert trend.avg_monthly_spend == 0.0
    assert len(trend.monthly_trend) == 12
    assert all(m.total_spend == 0.0 for m in trend.monthly_trend)

    # 2. Spend by Supplier
    sup_spend = service.get_spend_by_supplier(months=12)
    assert sup_spend.total_spend == 0.0
    assert len(sup_spend.suppliers) == 0

    # 3. Spend by Category
    cat_spend = service.get_spend_by_category(months=12)
    assert cat_spend.total_spend == 0.0
    assert len(cat_spend.categories) == 0


def test_spend_analytics_with_po_data(analytics_db):
    """
    QA Checklist item:
    Once PO data is received, spend aggregates compute accurately.
    """
    sup1 = Supplier(name="Organic Harvest Co")
    sup2 = Supplier(name="Apex Packaging")
    analytics_db.add_all([sup1, sup2])
    analytics_db.commit()

    cat1 = Category(name="Grains")
    cat2 = Category(name="Packaging")
    analytics_db.add_all([cat1, cat2])
    analytics_db.commit()

    p1 = Product(sku="GRAIN-1", name="Wheat", category_id=cat1.id, cost_price=40.0)
    p2 = Product(sku="BOX-1", name="Carton Box", category_id=cat2.id, cost_price=10.0)
    analytics_db.add_all([p1, p2])
    analytics_db.commit()

    # PO 1: Received from Sup1, 100 units of Wheat @ 40 = 4,000
    po1 = PurchaseOrder(
        po_number="PO-1001",
        supplier_id=sup1.id,
        status=POStatusEnum.RECEIVED,
        order_date=datetime(2026, 7, 15),
        total_amount=4000.0,
    )
    analytics_db.add(po1)
    analytics_db.commit()
    item1 = PurchaseOrderItem(
        po_id=po1.id,
        product_id=p1.id,
        qty_ordered=100.0,
        qty_received=100.0,
        unit_cost=40.0,
    )

    # PO 2: Received from Sup2, 200 units of Box @ 10 = 2,000
    po2 = PurchaseOrder(
        po_number="PO-1002",
        supplier_id=sup2.id,
        status=POStatusEnum.RECEIVED,
        order_date=datetime(2026, 8, 10),
        total_amount=2000.0,
    )
    analytics_db.add(po2)
    analytics_db.commit()
    item2 = PurchaseOrderItem(
        po_id=po2.id,
        product_id=p2.id,
        qty_ordered=200.0,
        qty_received=200.0,
        unit_cost=10.0,
    )

    analytics_db.add_all([item1, item2])
    analytics_db.commit()

    repo = SqlAlchemyStockAnalyticsRepository(session=analytics_db)
    service = StockAnalyticsService(analytics_repo=repo)

    # Spend Trend
    trend = service.get_spend_trend(months=12)
    assert trend.total_period_spend == 6000.0

    # Spend by Supplier
    sup_res = service.get_spend_by_supplier(months=12)
    assert sup_res.total_spend == 6000.0
    assert len(sup_res.suppliers) == 2
    # Sup 1: 4000 / 6000 = 66.7%
    assert sup_res.suppliers[0].supplier_name == "Organic Harvest Co"
    assert sup_res.suppliers[0].total_spend == 4000.0
    assert sup_res.suppliers[0].percentage == 66.7
    # Sup 2: 2000 / 6000 = 33.3%
    assert sup_res.suppliers[1].supplier_name == "Apex Packaging"
    assert sup_res.suppliers[1].total_spend == 2000.0
    assert sup_res.suppliers[1].percentage == 33.3

    # Spend by Category
    cat_res = service.get_spend_by_category(months=12)
    assert cat_res.total_spend == 6000.0
    assert len(cat_res.categories) == 2
    assert cat_res.categories[0].category_name == "Grains"
    assert cat_res.categories[0].total_spend == 4000.0
    assert cat_res.categories[0].percentage == 66.7


def test_product_cost_trend_flat_line_on_single_cost(analytics_db):
    """
    QA Checklist item:
    Avg-cost-trend chart correctly shows a flat line (pct_change = 0.0) for a product
    with only one recorded cost, not an error or NaN.
    """
    prod = Product(sku="SOLO-1", name="Solo Cost Item", cost_price=150.0)
    analytics_db.add(prod)
    analytics_db.commit()

    repo = SqlAlchemyStockAnalyticsRepository(session=analytics_db)
    service = StockAnalyticsService(analytics_repo=repo)

    trends = service.get_avg_cost_trend(product_ids=[prod.id])
    assert len(trends.products) == 1
    p_trend = trends.products[0]
    assert p_trend.sku == "SOLO-1"
    assert p_trend.current_cost_price == 150.0
    assert len(p_trend.cost_history) == 1
    assert p_trend.cost_history[0].cost_price == 150.0
    assert p_trend.pct_change == 0.0


def test_product_cost_trend_price_creep(analytics_db):
    """Verify price creep percentage calculation across multiple PO costs over time."""
    sup = Supplier(name="Spices Ltd")
    analytics_db.add(sup)
    analytics_db.commit()

    prod = Product(sku="PEPPER-1", name="Black Pepper", cost_price=200.0)
    analytics_db.add(prod)
    analytics_db.commit()

    # PO 1: Initial cost = 200
    po1 = PurchaseOrder(
        po_number="PO-201",
        supplier_id=sup.id,
        status=POStatusEnum.RECEIVED,
        order_date=datetime(2026, 1, 10),
    )
    analytics_db.add(po1)
    analytics_db.commit()
    item1 = PurchaseOrderItem(po_id=po1.id, product_id=prod.id, qty_ordered=50, qty_received=50, unit_cost=200.0)

    # PO 2: Crept cost = 250 (+25%)
    po2 = PurchaseOrder(
        po_number="PO-202",
        supplier_id=sup.id,
        status=POStatusEnum.RECEIVED,
        order_date=datetime(2026, 5, 20),
    )
    analytics_db.add(po2)
    analytics_db.commit()
    item2 = PurchaseOrderItem(po_id=po2.id, product_id=prod.id, qty_ordered=50, qty_received=50, unit_cost=250.0)

    analytics_db.add_all([item1, item2])
    analytics_db.commit()

    repo = SqlAlchemyStockAnalyticsRepository(session=analytics_db)
    service = StockAnalyticsService(analytics_repo=repo)

    trends = service.get_avg_cost_trend(product_ids=[prod.id])
    assert len(trends.products) == 1
    p_trend = trends.products[0]
    assert len(p_trend.cost_history) == 2
    assert p_trend.cost_history[0].cost_price == 200.0
    assert p_trend.cost_history[1].cost_price == 250.0
    assert p_trend.pct_change == 25.0


def test_spend_analytics_rest_endpoints(analytics_db, mock_user):
    """Integration test verifying all 4 FastAPI spend analytics endpoints."""
    test_app = FastAPI()
    test_app.include_router(stock_analytics_router.router)

    def override_get_current_user():
        return mock_user

    def override_get_service():
        repo = SqlAlchemyStockAnalyticsRepository(session=analytics_db)
        return StockAnalyticsService(analytics_repo=repo)

    test_app.dependency_overrides[get_current_user] = override_get_current_user
    test_app.dependency_overrides[stock_analytics_router.get_stock_analytics_service] = override_get_service

    client = TestClient(test_app)

    # 1. GET /analytics/stock/spend-trend
    r1 = client.get("/analytics/stock/spend-trend?months=12")
    assert r1.status_code == status.HTTP_200_OK
    assert "monthly_trend" in r1.json()

    # 2. GET /analytics/stock/spend-by-supplier
    r2 = client.get("/analytics/stock/spend-by-supplier?months=12")
    assert r2.status_code == status.HTTP_200_OK
    assert "suppliers" in r2.json()

    # 3. GET /analytics/stock/spend-by-category
    r3 = client.get("/analytics/stock/spend-by-category?months=12")
    assert r3.status_code == status.HTTP_200_OK
    assert "categories" in r3.json()

    # 4. GET /analytics/stock/avg-cost-trend
    r4 = client.get("/analytics/stock/avg-cost-trend")
    assert r4.status_code == status.HTTP_200_OK
    assert "products" in r4.json()

