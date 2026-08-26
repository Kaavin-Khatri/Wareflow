"""Automated unit and integration tests for Multi-Warehouse Batch Stock View (Step 5.3)."""

from datetime import date, timedelta

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.api.routers import stock as stock_router
from app.core.security import CurrentUser, get_current_user
from app.db.base import Base
from app.models.catalog import Category, Product
from app.models.uom import ProductUOMConversion, UnitOfMeasure
from app.models.warehouse import StockBatch, Warehouse
from app.repositories.impl.stock_repository import (
    InMemoryStockRepository,
    SqlAlchemyStockRepository,
)
from app.repositories.impl.uom_repository import SqlAlchemyUomRepository
from app.services.stock_service import StockService


@pytest.fixture
def stock_db():
    """Create in-memory SQLite database for Stock & Warehouse tests."""
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
        id="inventory-officer-1",
        email="inventory@wareflow.io",
        role="Manager",
        permissions={"inventory:view", "inventory:manage"},
    )


def test_dip_zero_service_code_changes_with_in_memory_stock_repository():
    """
    DIP Verification: Test that StockService functions identically when
    injected with InMemoryStockRepository vs SqlAlchemyStockRepository.
    """
    wh1 = {"id": "wh-1", "name": "Central Hub", "location": "Sector 4", "is_active": True}
    wh2 = {"id": "wh-2", "name": "North Annex", "location": "Sector 9", "is_active": True}
    prod1 = {
        "id": "prod-1",
        "sku": "BASMATI-5KG",
        "name": "Basmati Rice 5kg",
        "reorder_point": 100,
        "reorder_qty": 50,
        "cost_price": 40.0,
        "wholesale_price": 55.0,
        "is_active": True,
    }
    batches = [
        {
            "id": "b1",
            "product_id": "prod-1",
            "warehouse_id": "wh-1",
            "batch_no": "B100",
            "quantity": 60.0,
        },
        {
            "id": "b2",
            "product_id": "prod-1",
            "warehouse_id": "wh-2",
            "batch_no": "B101",
            "quantity": 25.0,
        },
    ]

    in_mem_repo = InMemoryStockRepository(
        warehouses=[wh1, wh2],
        products=[prod1],
        batches=batches,
    )
    service = StockService(stock_repo=in_mem_repo)

    # 1. Total on hand = 60 + 25 = 85
    total = in_mem_repo.get_on_hand("prod-1")
    assert total == 85.0

    # 2. Stock status: on_hand=85, reorder_point=100 -> 'low' (since > 25)
    stock_res = service.get_product_stock("prod-1")
    assert stock_res.total_on_hand == 85.0
    assert stock_res.stock_status == "low"
    assert len(stock_res.warehouses) == 2


def test_on_hand_totals_match_hand_calculated_sql_sum_for_3_spot_checked_products(stock_db):
    """
    QA Checklist item:
    Verify on-hand totals match a hand-run SQL SUM across stock_batches for 3 spot-checked products.
    """
    wh_main = Warehouse(name="Main Warehouse", location="Bhubaneswar", is_active=True)
    wh_sec = Warehouse(name="Secondary Depot", location="Cuttack", is_active=True)
    stock_db.add_all([wh_main, wh_sec])
    stock_db.commit()

    p1 = Product(
        sku="SPOT-1", name="Product 1", cost_price=10, wholesale_price=15, reorder_point=50
    )
    p2 = Product(
        sku="SPOT-2", name="Product 2", cost_price=20, wholesale_price=25, reorder_point=40
    )
    p3 = Product(
        sku="SPOT-3", name="Product 3", cost_price=30, wholesale_price=35, reorder_point=10
    )
    stock_db.add_all([p1, p2, p3])
    stock_db.commit()

    # Product 1: 50 in wh_main, 30 in wh_sec -> Total 80
    b1_1 = StockBatch(product_id=p1.id, warehouse_id=wh_main.id, batch_no="P1-B1", quantity=50.0)
    b1_2 = StockBatch(product_id=p1.id, warehouse_id=wh_sec.id, batch_no="P1-B2", quantity=30.0)

    # Product 2: 15 in wh_main, 10 in wh_main, 0 in wh_sec -> Total 25
    b2_1 = StockBatch(product_id=p2.id, warehouse_id=wh_main.id, batch_no="P2-B1", quantity=15.0)
    b2_2 = StockBatch(product_id=p2.id, warehouse_id=wh_main.id, batch_no="P2-B2", quantity=10.0)

    # Product 3: 2 in wh_sec -> Total 2
    b3_1 = StockBatch(product_id=p3.id, warehouse_id=wh_sec.id, batch_no="P3-B1", quantity=2.0)

    stock_db.add_all([b1_1, b1_2, b2_1, b2_2, b3_1])
    stock_db.commit()

    repo = SqlAlchemyStockRepository(session=stock_db)
    service = StockService(stock_repo=repo)

    # Hand sum spot checks
    assert repo.get_on_hand(p1.id) == 80.0
    assert repo.get_on_hand(p2.id) == 25.0
    assert repo.get_on_hand(p3.id) == 2.0

    # Per-warehouse spot checks
    assert repo.get_on_hand(p1.id, warehouse_id=wh_main.id) == 50.0
    assert repo.get_on_hand(p1.id, warehouse_id=wh_sec.id) == 30.0
    assert repo.get_on_hand(p2.id, warehouse_id=wh_main.id) == 25.0
    assert repo.get_on_hand(p2.id, warehouse_id=wh_sec.id) == 0.0

    # Service breakdown spot checks
    p1_stock = service.get_product_stock(p1.id)
    assert p1_stock.total_on_hand == 80.0
    assert len(p1_stock.batches) == 2


def test_stock_status_thresholds_ok_low_critical(stock_db):
    """
    QA Checklist item:
    Verify status calculation thresholds:
    - ok: on_hand > reorder_point
    - low: 0.25 * reorder_point < on_hand <= reorder_point
    - critical: on_hand <= 0.25 * reorder_point (or 0 / negative)
    """
    assert StockService.calculate_stock_status(on_hand=120, reorder_point=100) == "ok"
    assert StockService.calculate_stock_status(on_hand=100, reorder_point=100) == "low"
    assert StockService.calculate_stock_status(on_hand=50, reorder_point=100) == "low"
    assert StockService.calculate_stock_status(on_hand=26, reorder_point=100) == "low"
    assert StockService.calculate_stock_status(on_hand=25, reorder_point=100) == "critical"
    assert StockService.calculate_stock_status(on_hand=5, reorder_point=100) == "critical"
    assert StockService.calculate_stock_status(on_hand=0, reorder_point=100) == "critical"

    # Edge cases: reorder_point is 0
    assert StockService.calculate_stock_status(on_hand=10, reorder_point=0) == "ok"
    assert StockService.calculate_stock_status(on_hand=0, reorder_point=0) == "critical"


def test_warehouse_and_category_filtering(stock_db):
    """
    QA Checklist item:
    Filtering by warehouse or category narrows the stock overview feed correctly.
    """
    cat_grains = Category(name="Grains")
    cat_spices = Category(name="Spices")
    stock_db.add_all([cat_grains, cat_spices])
    stock_db.commit()

    wh_a = Warehouse(name="Warehouse A", is_active=True)
    wh_b = Warehouse(name="Warehouse B", is_active=True)
    stock_db.add_all([wh_a, wh_b])
    stock_db.commit()

    p_rice = Product(sku="RICE-01", name="Rice", category_id=cat_grains.id, reorder_point=50)
    p_chilli = Product(
        sku="CHILLI-01", name="Chilli Powder", category_id=cat_spices.id, reorder_point=20
    )
    stock_db.add_all([p_rice, p_chilli])
    stock_db.commit()

    b1 = StockBatch(product_id=p_rice.id, warehouse_id=wh_a.id, batch_no="RB1", quantity=100.0)
    b2 = StockBatch(product_id=p_rice.id, warehouse_id=wh_b.id, batch_no="RB2", quantity=40.0)
    b3 = StockBatch(product_id=p_chilli.id, warehouse_id=wh_b.id, batch_no="CB1", quantity=5.0)
    stock_db.add_all([b1, b2, b3])
    stock_db.commit()

    repo = SqlAlchemyStockRepository(session=stock_db)
    service = StockService(stock_repo=repo)

    # 1. Unfiltered: 2 products
    all_res = service.get_stock_overview()
    assert all_res.total_products == 2
    assert all_res.ok_count == 1  # Rice: 140 > 50
    assert all_res.critical_count == 1  # Chilli: 5 <= 0.25*20 (5)

    # 2. Filter by Category = Spices: 1 product
    spice_res = service.get_stock_overview(category_id=cat_spices.id)
    assert len(spice_res.items) == 1
    assert spice_res.items[0].sku == "CHILLI-01"

    # 3. Filter by Warehouse A:
    # Rice only has 100 in WH A
    wh_a_res = service.get_stock_overview(warehouse_id=wh_a.id)
    assert len(wh_a_res.items) == 2
    rice_wh_a = next(i for i in wh_a_res.items if i.sku == "RICE-01")
    assert rice_wh_a.total_on_hand == 100.0

    # 4. Filter by Status = critical:
    crit_res = service.get_stock_overview(status_filter="critical")
    assert len(crit_res.items) == 1
    assert crit_res.items[0].sku == "CHILLI-01"


def test_batches_expiring_soon(stock_db):
    """Verify get_batches_expiring_soon retrieves batches expiring within horizon."""
    wh = Warehouse(name="Pharma Warehouse", is_active=True)
    stock_db.add(wh)
    stock_db.commit()

    prod = Product(sku="EXP-TEST", name="Dairy Milk", reorder_point=10)
    stock_db.add(prod)
    stock_db.commit()

    today = date.today()
    # Batch 1: Expiring in 10 days
    b1 = StockBatch(
        product_id=prod.id,
        warehouse_id=wh.id,
        batch_no="EXP10",
        quantity=20.0,
        expiry_date=today + timedelta(days=10),
    )
    # Batch 2: Expiring in 45 days
    b2 = StockBatch(
        product_id=prod.id,
        warehouse_id=wh.id,
        batch_no="EXP45",
        quantity=30.0,
        expiry_date=today + timedelta(days=45),
    )
    # Batch 3: Already expired (5 days ago)
    b3 = StockBatch(
        product_id=prod.id,
        warehouse_id=wh.id,
        batch_no="EXPPASSED",
        quantity=10.0,
        expiry_date=today - timedelta(days=5),
    )
    # Batch 4: Expiring in 20 days but 0 qty
    b4 = StockBatch(
        product_id=prod.id,
        warehouse_id=wh.id,
        batch_no="EXPZERO",
        quantity=0.0,
        expiry_date=today + timedelta(days=20),
    )

    stock_db.add_all([b1, b2, b3, b4])
    stock_db.commit()

    repo = SqlAlchemyStockRepository(session=stock_db)
    service = StockService(stock_repo=repo)

    expiring = service.get_batches_expiring_soon(days=30)
    # Should include b3 (already expired) and b1 (expiring in 10 days), but NOT b2 (>30d) and NOT b4 (0 qty)
    batch_nos = [b.batch_no for b in expiring]
    assert "EXP10" in batch_nos
    assert "EXPPASSED" in batch_nos
    assert "EXP45" not in batch_nos
    assert "EXPZERO" not in batch_nos


def test_stock_api_endpoints_lifecycle(stock_db, mock_user):
    """Integration test verifying FastAPI stock endpoints."""
    test_app = FastAPI()
    test_app.include_router(stock_router.router)

    def override_get_current_user():
        return mock_user

    def override_get_stock_service():
        repo = SqlAlchemyStockRepository(session=stock_db)
        uom_repo = SqlAlchemyUomRepository(session=stock_db)
        return StockService(stock_repo=repo, uom_repo=uom_repo)

    test_app.dependency_overrides[get_current_user] = override_get_current_user
    test_app.dependency_overrides[stock_router.get_stock_service] = override_get_stock_service

    client = TestClient(test_app)

    # 1. Create warehouse, UoM, product, and stock batches in DB
    wh = Warehouse(name="North Central Hub", location="Sector 1", is_active=True)
    uom_pcs = UnitOfMeasure(name="Piece", abbreviation="pcs")
    uom_cs = UnitOfMeasure(name="Case", abbreviation="cs")
    stock_db.add_all([wh, uom_pcs, uom_cs])
    stock_db.commit()

    prod = Product(
        sku="TEST-API-STK",
        name="Premium Almonds 500g",
        base_uom_id=uom_pcs.id,
        cost_price=100.0,
        wholesale_price=140.0,
        reorder_point=40,
        reorder_qty=100,
    )
    stock_db.add(prod)
    stock_db.commit()

    # 1 Case = 20 Pieces
    conv = ProductUOMConversion(
        product_id=prod.id,
        from_uom_id=uom_cs.id,
        to_uom_id=uom_pcs.id,
        factor=20.0,
    )
    batch = StockBatch(
        product_id=prod.id,
        warehouse_id=wh.id,
        batch_no="ALM-2026-B1",
        quantity=100.0,
        expiry_date=date.today() + timedelta(days=90),
    )
    stock_db.add_all([conv, batch])
    stock_db.commit()

    # 2. GET /stock/warehouses
    res_wh = client.get("/stock/warehouses")
    assert res_wh.status_code == status.HTTP_200_OK
    assert len(res_wh.json()) >= 1
    assert res_wh.json()[0]["name"] == "North Central Hub"

    # 3. GET /stock/overview
    res_ov = client.get("/stock/overview")
    assert res_ov.status_code == status.HTTP_200_OK
    ov_data = res_ov.json()
    assert ov_data["total_products"] == 1
    assert ov_data["ok_count"] == 1
    item = ov_data["items"][0]
    assert item["sku"] == "TEST-API-STK"
    assert item["total_on_hand"] == 100.0
    assert item["preferred_uom_name"] == "Case"
    assert item["preferred_uom_qty"] == 5.0  # 100 / 20 = 5 Cases
    assert item["stock_status"] == "ok"

    # 4. GET /products/{id}/stock
    res_prod = client.get(f"/products/{prod.id}/stock")
    assert res_prod.status_code == status.HTTP_200_OK
    prod_data = res_prod.json()
    assert prod_data["total_on_hand"] == 100.0
    assert len(prod_data["batches"]) == 1
    assert prod_data["batches"][0]["batch_no"] == "ALM-2026-B1"
    assert prod_data["batches"][0]["days_until_expiry"] == 90

    # 5. GET /stock/expiring
    res_exp = client.get("/stock/expiring?days=100")
    assert res_exp.status_code == status.HTTP_200_OK
    assert len(res_exp.json()) == 1

    # 6. GET /stock/batches
    res_batches = client.get("/stock/batches")
    assert res_batches.status_code == status.HTTP_200_OK
    batches_data = res_batches.json()
    assert len(batches_data) == 1
    assert batches_data[0]["batch_no"] == "ALM-2026-B1"
    assert batches_data[0]["quantity"] == 100.0
    assert batches_data[0]["product_id"] == prod.id

