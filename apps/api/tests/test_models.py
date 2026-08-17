"""Automated tests for SQLAlchemy wholesale distribution domain models."""

from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.catalog import Product
from app.models.inventory import StockMovement, StockMovementTypeEnum
from app.models.notification import Notification
from app.models.retailer import Retailer, SalesOrder, SalesOrderItem, SOStatusEnum
from app.models.supplier import POStatusEnum, PurchaseOrder, PurchaseOrderItem, Supplier
from app.models.uom import ProductUOMConversion, UnitOfMeasure
from app.models.warehouse import StockBatch, Warehouse


@pytest.fixture
def db_session():
    """Create an isolated in-memory SQLite database session for model testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def test_units_of_measure_and_conversions(db_session: Session):
    """Test UOM creation and conversion factor relationship."""
    piece = UnitOfMeasure(name="Piece", abbreviation="pcs")
    box = UnitOfMeasure(name="Box", abbreviation="box")
    db_session.add_all([piece, box])
    db_session.flush()

    product = Product(sku="SKU-CHIPS-01", name="Potato Chips 50g", base_uom_id=piece.id)
    db_session.add(product)
    db_session.flush()

    conv = ProductUOMConversion(
        product_id=product.id,
        from_uom_id=box.id,
        to_uom_id=piece.id,
        factor=24.0,
    )
    db_session.add(conv)
    db_session.commit()

    saved_conv = db_session.query(ProductUOMConversion).first()
    assert saved_conv is not None
    assert float(saved_conv.factor) == 24.0
    assert saved_conv.from_uom.abbreviation == "box"
    assert saved_conv.to_uom.abbreviation == "pcs"


def test_supplier_and_purchase_order_flow(db_session: Session):
    """Test supplier, PO status enum (ready_for_dispatch), and line items."""
    supplier = Supplier(
        name="Amul Dairy Ltd",
        contact_person="Ramesh Patel",
        phone="+919876543210",
        gstin="24AAACA1234A1Z5",
        fssai_license_no="10012021000123",
        fssai_expiry_date=date(2028, 12, 31),
    )
    db_session.add(supplier)
    db_session.flush()

    product = Product(sku="SKU-BUTTER-500", name="Amul Butter 500g", cost_price=240.00)
    db_session.add(product)
    db_session.flush()

    po = PurchaseOrder(
        po_number="PO-202608-001",
        supplier_id=supplier.id,
        status=POStatusEnum.READY_FOR_DISPATCH,
        total_amount=24000.00,
    )
    po_item = PurchaseOrderItem(
        purchase_order=po,
        product_id=product.id,
        qty_ordered=100.0,
        qty_received=0.0,
        unit_cost=240.00,
    )
    po.items.append(po_item)
    db_session.add(po)
    db_session.commit()

    saved_po = db_session.query(PurchaseOrder).filter_by(po_number="PO-202608-001").first()
    assert saved_po is not None
    assert saved_po.status == POStatusEnum.READY_FOR_DISPATCH
    assert len(saved_po.items) == 1
    assert saved_po.items[0].product.name == "Amul Butter 500g"


def test_retailer_credit_and_sales_order(db_session: Session):
    """Test retailer credit tracking and sales order lifecycle."""
    retailer = Retailer(
        name="Krishna Supermarket",
        credit_limit=50000.00,
        credit_balance=12000.00,
        pricing_tier="wholesale_tier_1",
    )
    db_session.add(retailer)
    db_session.flush()

    product = Product(sku="SKU-GHEE-1L", name="Pure Cow Ghee 1L", wholesale_price=550.00)
    db_session.add(product)
    db_session.flush()

    so = SalesOrder(
        so_number="SO-202608-001",
        retailer_id=retailer.id,
        status=SOStatusEnum.CONFIRMED,
        total_amount=11000.00,
    )
    so_item = SalesOrderItem(
        sales_order=so,
        product_id=product.id,
        qty=20.0,
        unit_price=550.00,
    )
    so.items.append(so_item)
    db_session.add(so)
    db_session.commit()

    saved_so = db_session.query(SalesOrder).filter_by(so_number="SO-202608-001").first()
    assert saved_so is not None
    assert saved_so.retailer.credit_limit == 50000.00
    assert saved_so.status == SOStatusEnum.CONFIRMED


def test_warehouse_batches_and_stock_ledger(db_session: Session):
    """Test batch tracking and append-only stock movement ledger."""
    warehouse = Warehouse(name="Main Central Warehouse", location="Bhiwandi Hub 1")
    product = Product(sku="SKU-OIL-1L", name="Sunflower Oil 1L", cost_price=110.00)
    db_session.add_all([warehouse, product])
    db_session.flush()

    batch = StockBatch(
        product_id=product.id,
        warehouse_id=warehouse.id,
        batch_no="BATCH-2026-AUG-01",
        quantity=500.0,
        expiry_date=date(2027, 8, 1),
    )
    db_session.add(batch)
    db_session.flush()

    movement = StockMovement(
        product_id=product.id,
        warehouse_id=warehouse.id,
        batch_id=batch.id,
        type=StockMovementTypeEnum.IN,
        quantity=500.0,
        reference_type="purchase_order",
        reference_id="PO-202608-001",
        created_by="system",
    )
    db_session.add(movement)

    notification = Notification(
        user_id="user_admin_1",
        type="reorder_alert",
        title="Low Stock Alert",
        body="Sunflower Oil 1L is below reorder point.",
    )
    db_session.add(notification)
    db_session.commit()

    saved_movement = db_session.query(StockMovement).first()
    assert saved_movement is not None
    assert saved_movement.type == StockMovementTypeEnum.IN
    assert float(saved_movement.quantity) == 500.0
    assert saved_movement.batch.batch_no == "BATCH-2026-AUG-01"

    saved_notif = db_session.query(Notification).first()
    assert saved_notif.is_read is False
