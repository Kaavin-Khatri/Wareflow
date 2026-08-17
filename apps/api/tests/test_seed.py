"""Automated tests for database seeding idempotency and business rules (Step 2.4)."""

import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

# Add repo root to path for scripts.seed import
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.seed import (
    get_or_create_category,
    get_or_create_permission,
    get_or_create_role,
    get_or_create_uom,
    get_or_create_warehouse,
    sync_role_permission,
    upsert_product,
    upsert_retailer,
    upsert_stock_batch,
    upsert_supplier,
)

from app.db.base import Base
from app.models import (
    Product,
    Role,
    StockBatch,
    Warehouse,
)


@pytest.fixture
def seed_session():
    """Create an isolated in-memory SQLite database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def run_full_seed(db: Session):
    """Execute standard seed dataset against the provided session."""
    uom_pcs = get_or_create_uom(db, "Piece", "pcs")
    _ = get_or_create_uom(db, "Case (24 pcs)", "case")

    wh1 = get_or_create_warehouse(db, "Bhiwandi Central Hub", "Bhiwandi, MH")
    _ = get_or_create_warehouse(db, "Navi Mumbai APMC Terminal", "Vashi, Navi Mumbai, MH")

    _ = upsert_supplier(
        db,
        "HUL",
        "Rajesh",
        "+912239830000",
        "sales@hul.com",
        "Mumbai",
        "27AAACH2702H1Z1",
        "10012022000245",
        None,
    )

    _ = upsert_retailer(
        db,
        "Aapla Supermarket",
        "Mahesh",
        "+919820112233",
        "a@a.com",
        "Kharghar",
        "27AABCU9603R1ZM",
        "wholesale_gold",
        250000.0,
        48500.0,
    )

    cat = get_or_create_category(db, "Staples & Grains")

    p1 = upsert_product(
        db,
        "SKU-1",
        "Basmati Rice 5kg",
        "Rice",
        "100630",
        "8901001",
        cat.id,
        uom_pcs.id,
        320,
        380,
        50,
        100,
    )
    p2 = upsert_product(
        db,
        "SKU-2",
        "Tata Tea Gold 1kg",
        "Tea",
        "090240",
        "8901002",
        cat.id,
        uom_pcs.id,
        460,
        540,
        40,
        80,
    )
    p3 = upsert_product(
        db,
        "SKU-3",
        "Nescafe Coffee 200g",
        "Coffee",
        "210111",
        "8901003",
        cat.id,
        uom_pcs.id,
        480,
        575,
        25,
        50,
    )
    p4 = upsert_product(
        db,
        "SKU-4",
        "Kissan Jam 1kg",
        "Jam",
        "200799",
        "8901004",
        cat.id,
        uom_pcs.id,
        210,
        255,
        30,
        60,
    )
    p5 = upsert_product(
        db,
        "SKU-5",
        "Parle-G 800g",
        "Biscuit",
        "190531",
        "8901005",
        cat.id,
        uom_pcs.id,
        65,
        78,
        100,
        200,
    )

    # 3 deliberate low-stock products (SKU-2, SKU-3, SKU-4)
    upsert_stock_batch(db, p1.id, wh1.id, "B1", 150.0)  # Healthy stock: 150 > 50
    upsert_stock_batch(db, p2.id, wh1.id, "B2", 10.0)  # Low stock: 10 < 40
    upsert_stock_batch(db, p3.id, wh1.id, "B3", 5.0)  # Low stock: 5 < 25
    upsert_stock_batch(db, p4.id, wh1.id, "B4", 8.0)  # Low stock: 8 < 30
    upsert_stock_batch(db, p5.id, wh1.id, "B5", 300.0)  # Healthy stock: 300 > 100

    # 5 Roles & Permissions
    roles_list = ["Owner", "Manager", "Sales Staff", "Warehouse Staff", "Accountant"]
    perm = get_or_create_permission(db, "inventory:view", "View stock")
    for rname in roles_list:
        r = get_or_create_role(db, rname, f"{rname} role")
        sync_role_permission(db, r.id, perm.id)

    db.commit()


def test_seed_idempotency_and_row_counts(seed_session: Session):
    """Test that running the seed twice yields identical table counts (idempotency)."""
    # First seed run
    run_full_seed(seed_session)

    wh_count_1 = seed_session.scalar(select(func.count(Warehouse.id)))
    prod_count_1 = seed_session.scalar(select(func.count(Product.id)))
    batch_count_1 = seed_session.scalar(select(func.count(StockBatch.id)))
    role_count_1 = seed_session.scalar(select(func.count(Role.id)))

    # Second seed run
    run_full_seed(seed_session)

    wh_count_2 = seed_session.scalar(select(func.count(Warehouse.id)))
    prod_count_2 = seed_session.scalar(select(func.count(Product.id)))
    batch_count_2 = seed_session.scalar(select(func.count(StockBatch.id)))
    role_count_2 = seed_session.scalar(select(func.count(Role.id)))

    assert wh_count_1 == wh_count_2 == 2
    assert prod_count_1 == prod_count_2 == 5
    assert batch_count_1 == batch_count_2 == 5
    assert role_count_1 == role_count_2 == 5


def test_low_stock_seeded_products(seed_session: Session):
    """Test that at least 3 seeded products sit below their reorder_point on purpose."""
    run_full_seed(seed_session)

    # Query products with total batch stock below reorder_point
    products = seed_session.execute(select(Product)).scalars().all()
    low_stock_prods = []
    for prod in products:
        batches = (
            seed_session.execute(select(StockBatch).where(StockBatch.product_id == prod.id))
            .scalars()
            .all()
        )
        total_qty = sum(b.quantity for b in batches)
        if total_qty < prod.reorder_point:
            low_stock_prods.append((prod.sku, total_qty, prod.reorder_point))

    assert len(low_stock_prods) >= 3
    assert any(p[0] == "SKU-2" for p in low_stock_prods)
    assert any(p[0] == "SKU-3" for p in low_stock_prods)
    assert any(p[0] == "SKU-4" for p in low_stock_prods)


def test_default_roles_and_permissions(seed_session: Session):
    """Test that 5 default roles exist with sane permissions."""
    run_full_seed(seed_session)

    roles = seed_session.execute(select(Role)).scalars().all()
    role_names = {r.name for r in roles}
    assert {"Owner", "Manager", "Sales Staff", "Warehouse Staff", "Accountant"}.issubset(role_names)

    for role in roles:
        assert len(role.permissions) >= 1
