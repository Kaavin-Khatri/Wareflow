"""Unit and integration tests for Purchase Orders and Authoritative Goods Receiving (Step 7.2)."""

from datetime import date, timedelta

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routers import purchase_orders as po_router
from app.core.security import CurrentUser, get_current_user
from app.db.base import Base
from app.models.catalog import Product
from app.models.inventory import StockMovement, StockMovementTypeEnum
from app.models.supplier import POStatusEnum, Supplier
from app.models.uom import ProductUOMConversion, UnitOfMeasure
from app.models.warehouse import StockBatch, Warehouse
from app.repositories.impl.product_repository import (
    InMemoryProductRepository,
    SqlAlchemyProductRepository,
)
from app.repositories.impl.purchase_order_repository import (
    InMemoryPurchaseOrderRepository,
    SqlAlchemyPurchaseOrderRepository,
)
from app.repositories.impl.stock_repository import (
    InMemoryStockRepository,
    SqlAlchemyStockRepository,
)
from app.repositories.impl.supplier_repository import (
    InMemorySupplierRepository,
    SqlAlchemySupplierRepository,
)
from app.repositories.impl.uom_repository import InMemoryUomRepository, SqlAlchemyUomRepository
from app.schemas.purchase_orders import (
    POCreateRequest,
    POItemCreateRequest,
    POItemUpdateRequest,
    POReceiveItemRequest,
    POReceiveRequest,
    POUpdateRequest,
)
from app.services.purchase_order_service import PurchaseOrderService
from app.services.stock_service import StockService
from app.services.uom_service import UomService


@pytest.fixture
def po_db():
    """In-memory SQLite session with full schema initialized."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def mock_admin_user():
    return CurrentUser(
        id="user-po-admin",
        email="admin@wareflow.io",
        display_name="Operations Manager",
        role="Admin",
        permissions={
            "inventory:view",
            "inventory:manage",
        },
    )


def test_in_memory_po_lifecycle_and_status_transitions():
    """Verify Draft PO creation, modification guards, and ordering transition."""
    supplier = Supplier(
        id="sup-1",
        name="Tata Consumer Products",
        is_active=True,
    )
    supplier_repo = InMemorySupplierRepository([supplier])

    product = Product(
        id="prod-1",
        sku="TEA-TATA-500G",
        name="Tata Tea Premium 500g",
        cost_price=120.0,
        is_active=True,
    )
    product_repo = InMemoryProductRepository([product])
    po_repo = InMemoryPurchaseOrderRepository()
    stock_repo = InMemoryStockRepository(
        warehouses=[{"id": "wh-1", "name": "Main Hub", "is_active": True}],
        products=[
            {
                "id": "prod-1",
                "sku": "TEA-TATA-500G",
                "name": "Tata Tea Premium 500g",
                "is_active": True,
            }
        ],
    )
    stock_service = StockService(stock_repo=stock_repo)
    po_service = PurchaseOrderService(
        po_repo=po_repo,
        supplier_repo=supplier_repo,
        product_repo=product_repo,
        stock_service=stock_service,
    )

    # 1. Create Draft PO
    create_payload = POCreateRequest(
        supplier_id="sup-1",
        expected_date=date.today() + timedelta(days=7),
        items=[
            POItemCreateRequest(
                product_id="prod-1",
                qty_ordered=100.0,
                unit_cost=115.0,
            )
        ],
    )
    draft_po = po_service.create_draft_po(create_payload, actor_id="user-1")
    assert draft_po.status == POStatusEnum.DRAFT
    assert draft_po.total_amount == 11500.0
    assert len(draft_po.items) == 1

    # 2. Update Draft PO (change qty)
    update_payload = POUpdateRequest(
        items=[
            POItemUpdateRequest(
                product_id="prod-1",
                qty_ordered=120.0,
                unit_cost=110.0,
            )
        ]
    )
    updated_po = po_service.update_draft_po(draft_po.id, update_payload, actor_id="user-1")
    assert updated_po.total_amount == 13200.0
    assert updated_po.items[0].qty_ordered == 120.0

    # 3. Transition Draft -> Ordered
    ordered_po = po_service.transition_to_ordered(draft_po.id, actor_id="user-1")
    assert ordered_po.status == POStatusEnum.ORDERED

    # 4. Guard: Cannot edit once ordered
    with pytest.raises(Exception) as exc_info:
        po_service.update_draft_po(draft_po.id, update_payload, actor_id="user-1")
    assert "Only draft purchase orders can be modified" in str(exc_info.value)


def test_po_goods_receiving_with_uom_conversion():
    """
    Verify authoritative single-door goods receiving:
    - Ordered in Cases (1 Case = 10 Pieces base)
    - Partial receive: 2 Cases -> 20 base units in StockBatch & StockMovement(type=in)
    - Full receive: remaining 3 Cases -> PO status transitions to received
    """
    uom_piece = UnitOfMeasure(id="uom-pc", name="Piece", abbreviation="pc")
    uom_case = UnitOfMeasure(id="uom-cs", name="Case", abbreviation="cs")
    uom_repo = InMemoryUomRepository(
        seed_uoms=[uom_piece, uom_case],
        seed_products=[{"id": "prod-oil", "base_uom_id": "uom-pc"}],
        seed_conversions=[
            ProductUOMConversion(
                id="conv-1",
                product_id="prod-oil",
                from_uom_id="uom-cs",
                to_uom_id="uom-pc",
                factor=10.0,
            )
        ],
    )

    uom_service = UomService(uom_repo=uom_repo)

    supplier = Supplier(id="sup-oil", name="Fortune Oil Mills", is_active=True)
    supplier_repo = InMemorySupplierRepository([supplier])

    product = Product(
        id="prod-oil",
        sku="OIL-SUN-1L",
        name="Fortune Sunflower Oil 1L",
        base_uom_id="uom-pc",
        cost_price=140.0,
        is_active=True,
    )
    product_repo = InMemoryProductRepository([product])

    stock_repo = InMemoryStockRepository(
        warehouses=[{"id": "wh-central", "name": "Central Depot", "is_active": True}],
        products=[
            {
                "id": "prod-oil",
                "sku": "OIL-SUN-1L",
                "name": "Fortune Sunflower Oil 1L",
                "is_active": True,
            }
        ],
    )
    stock_service = StockService(stock_repo=stock_repo, uom_repo=uom_repo, uom_service=uom_service)
    po_repo = InMemoryPurchaseOrderRepository()
    po_service = PurchaseOrderService(
        po_repo=po_repo,
        supplier_repo=supplier_repo,
        product_repo=product_repo,
        stock_service=stock_service,
    )

    # 1. Create PO for 5 Cases
    po = po_service.create_draft_po(
        POCreateRequest(
            supplier_id="sup-oil",
            items=[
                POItemCreateRequest(
                    product_id="prod-oil",
                    qty_ordered=5.0,
                    unit_cost=1400.0,
                    uom_id="uom-cs",
                )
            ],
        )
    )
    po_item_id = po.items[0].id

    # 2. Place Order
    po_service.transition_to_ordered(po.id)

    # 3. Receive Partial: 2 Cases
    receive_payload_1 = POReceiveRequest(
        items=[
            POReceiveItemRequest(
                po_item_id=po_item_id,
                qty_received=2.0,
                uom_id="uom-cs",
                batch_no="BATCH-AUG-01",
                expiry_date=date(2027, 8, 1),
                warehouse_id="wh-central",
            )
        ]
    )
    partially_received_po = po_service.receive_goods(po.id, receive_payload_1, actor_id="user-1")

    # PO status must be PARTIALLY_RECEIVED
    assert partially_received_po.status == POStatusEnum.PARTIALLY_RECEIVED
    assert partially_received_po.items[0].qty_received == 2.0

    # Stock on hand in base UoM must be exactly 20 Pieces (2 cases * 10)
    assert stock_repo.get_on_hand("prod-oil", "wh-central") == 20.0

    # 4. Receive Remaining: 3 Cases
    receive_payload_2 = POReceiveRequest(
        items=[
            POReceiveItemRequest(
                po_item_id=po_item_id,
                qty_received=3.0,
                uom_id="uom-cs",
                batch_no="BATCH-AUG-02",
                expiry_date=date(2027, 9, 1),
                warehouse_id="wh-central",
            )
        ]
    )
    fully_received_po = po_service.receive_goods(po.id, receive_payload_2, actor_id="user-1")

    # PO status must be RECEIVED
    assert fully_received_po.status == POStatusEnum.RECEIVED
    assert fully_received_po.items[0].qty_received == 5.0

    # Total stock on hand must now be exactly 50 Pieces (5 cases * 10)
    assert stock_repo.get_on_hand("prod-oil", "wh-central") == 50.0


def test_po_receiving_guards(po_db):
    """Test validations: cannot receive more than ordered, cannot receive on draft PO."""
    uom = UnitOfMeasure(name="Kilogram", abbreviation="kg")
    po_db.add(uom)
    wh = Warehouse(name="North Warehouse", is_active=True)
    po_db.add(wh)
    sup = Supplier(name="Amul Dairy", is_active=True)
    po_db.add(sup)
    prod = Product(sku="BUTTER-500G", name="Amul Butter", base_uom_id=uom.id, cost_price=250.0)
    po_db.add(prod)
    po_db.commit()

    po_repo = SqlAlchemyPurchaseOrderRepository(po_db)
    supplier_repo = SqlAlchemySupplierRepository(po_db)
    product_repo = SqlAlchemyProductRepository(po_db)
    stock_repo = SqlAlchemyStockRepository(po_db)
    uom_repo = SqlAlchemyUomRepository(po_db)
    stock_service = StockService(stock_repo=stock_repo, uom_repo=uom_repo)
    po_service = PurchaseOrderService(
        po_repo=po_repo,
        supplier_repo=supplier_repo,
        product_repo=product_repo,
        stock_service=stock_service,
    )

    po = po_service.create_draft_po(
        POCreateRequest(
            supplier_id=sup.id,
            items=[
                POItemCreateRequest(
                    product_id=prod.id,
                    qty_ordered=10.0,
                    unit_cost=240.0,
                    uom_id=uom.id,
                )
            ],
        )
    )
    item_id = po.items[0].id

    # 1. Error when receiving on DRAFT PO
    with pytest.raises(Exception) as exc1:
        po_service.receive_goods(
            po.id,
            POReceiveRequest(
                items=[
                    POReceiveItemRequest(
                        po_item_id=item_id,
                        qty_received=5.0,
                        batch_no="B1",
                        warehouse_id=wh.id,
                    )
                ]
            ),
        )
    assert "Order must be placed first" in str(exc1.value)

    # Transition to ORDERED
    po_service.transition_to_ordered(po.id)

    # 2. Error when over-receiving
    with pytest.raises(Exception) as exc2:
        po_service.receive_goods(
            po.id,
            POReceiveRequest(
                items=[
                    POReceiveItemRequest(
                        po_item_id=item_id,
                        qty_received=15.0,  # ordered only 10
                        batch_no="B1",
                        warehouse_id=wh.id,
                    )
                ]
            ),
        )
    assert "Only 10.0 units remain pending" in str(exc2.value)


def test_sqlalchemy_po_persistence_and_stock_ledger(po_db):
    """Test full SQLAlchemy database persistence, stock batch upsert, and StockMovement(type=in) record."""
    uom = UnitOfMeasure(name="Liter", abbreviation="L")
    po_db.add(uom)
    wh = Warehouse(name="South Warehouse", is_active=True)
    po_db.add(wh)
    sup = Supplier(name="Nestle India", is_active=True)
    po_db.add(sup)
    prod = Product(sku="MILK-1L", name="Nestle A+ Milk", base_uom_id=uom.id, cost_price=75.0)
    po_db.add(prod)
    po_db.commit()

    po_repo = SqlAlchemyPurchaseOrderRepository(po_db)
    supplier_repo = SqlAlchemySupplierRepository(po_db)
    product_repo = SqlAlchemyProductRepository(po_db)
    stock_repo = SqlAlchemyStockRepository(po_db)
    uom_repo = SqlAlchemyUomRepository(po_db)
    stock_service = StockService(stock_repo=stock_repo, uom_repo=uom_repo)
    po_service = PurchaseOrderService(
        po_repo=po_repo,
        supplier_repo=supplier_repo,
        product_repo=product_repo,
        stock_service=stock_service,
    )

    po = po_service.create_draft_po(
        POCreateRequest(
            supplier_id=sup.id,
            expected_date=date.today() + timedelta(days=5),
            items=[
                POItemCreateRequest(
                    product_id=prod.id,
                    qty_ordered=50.0,
                    unit_cost=70.0,
                    uom_id=uom.id,
                )
            ],
        )
    )
    item_id = po.items[0].id

    po_service.transition_to_ordered(po.id)

    # Receive full 50L
    expiry = date.today() + timedelta(days=90)
    po_service.receive_goods(
        po.id,
        POReceiveRequest(
            items=[
                POReceiveItemRequest(
                    po_item_id=item_id,
                    qty_received=50.0,
                    batch_no="NESTLE-B99",
                    expiry_date=expiry,
                    warehouse_id=wh.id,
                )
            ]
        ),
        actor_id="user-test",
    )

    # Verify StockBatch created
    saved_batch = po_db.query(StockBatch).filter_by(batch_no="NESTLE-B99").first()
    assert saved_batch is not None
    assert float(saved_batch.quantity) == 50.0
    assert saved_batch.expiry_date == expiry

    # Verify StockMovement(type=in) created
    saved_movement = po_db.query(StockMovement).filter_by(reference_id=po.id).first()
    assert saved_movement is not None
    assert saved_movement.type == StockMovementTypeEnum.IN
    assert float(saved_movement.quantity) == 50.0
    assert saved_movement.product_id == prod.id
    assert saved_movement.warehouse_id == wh.id
    assert saved_movement.created_by == "user-test"


def test_purchase_orders_rest_endpoints(po_db, mock_admin_user):
    """Test FastAPI REST endpoints for purchase orders."""
    test_app = FastAPI()
    test_app.include_router(po_router.router)

    uom = UnitOfMeasure(name="Box", abbreviation="box")
    po_db.add(uom)
    wh = Warehouse(name="East Hub", is_active=True)
    po_db.add(wh)
    sup = Supplier(name="Dabur India", is_active=True)
    po_db.add(sup)
    prod = Product(sku="HONEY-500G", name="Dabur Honey 500g", base_uom_id=uom.id, cost_price=180.0)
    po_db.add(prod)
    po_db.commit()

    po_repo = SqlAlchemyPurchaseOrderRepository(po_db)
    supplier_repo = SqlAlchemySupplierRepository(po_db)
    product_repo = SqlAlchemyProductRepository(po_db)
    stock_repo = SqlAlchemyStockRepository(po_db)
    uom_repo = SqlAlchemyUomRepository(po_db)
    stock_service = StockService(stock_repo=stock_repo, uom_repo=uom_repo)
    service = PurchaseOrderService(
        po_repo=po_repo,
        supplier_repo=supplier_repo,
        product_repo=product_repo,
        stock_service=stock_service,
    )

    test_app.dependency_overrides[get_current_user] = lambda: mock_admin_user
    test_app.dependency_overrides[po_router.get_purchase_order_service] = lambda: service

    client = TestClient(test_app)

    # 1. POST /purchase-orders (Create Draft)
    res_create = client.post(
        "/purchase-orders",
        json={
            "supplier_id": sup.id,
            "expected_date": str(date.today() + timedelta(days=10)),
            "items": [
                {
                    "product_id": prod.id,
                    "qty_ordered": 20.0,
                    "unit_cost": 175.0,
                    "uom_id": uom.id,
                }
            ],
        },
    )
    assert res_create.status_code == status.HTTP_201_CREATED
    po_data = res_create.json()
    po_id = po_data["id"]
    po_item_id = po_data["items"][0]["id"]
    assert po_data["status"] == "draft"
    assert po_data["total_amount"] == 3500.0

    # 2. GET /purchase-orders (List)
    res_list = client.get("/purchase-orders")
    assert res_list.status_code == status.HTTP_200_OK
    assert len(res_list.json()) == 1

    # 3. GET /purchase-orders/{id}
    res_get = client.get(f"/purchase-orders/{po_id}")
    assert res_get.status_code == status.HTTP_200_OK
    assert res_get.json()["po_number"] == po_data["po_number"]

    # 4. PATCH /purchase-orders/{id} (Edit draft items)
    res_patch = client.patch(
        f"/purchase-orders/{po_id}",
        json={
            "items": [
                {
                    "product_id": prod.id,
                    "qty_ordered": 30.0,
                    "unit_cost": 170.0,
                    "uom_id": uom.id,
                }
            ]
        },
    )
    assert res_patch.status_code == status.HTTP_200_OK
    assert res_patch.json()["total_amount"] == 5100.0
    po_item_id = res_patch.json()["items"][0]["id"]

    # 5. POST /purchase-orders/{id}/order (Place Order)
    res_order = client.post(f"/purchase-orders/{po_id}/order")
    assert res_order.status_code == status.HTTP_200_OK
    assert res_order.json()["status"] == "ordered"

    # 6. POST /purchase-orders/{id}/receive (Receive Goods)
    res_receive = client.post(
        f"/purchase-orders/{po_id}/receive",
        json={
            "items": [
                {
                    "po_item_id": po_item_id,
                    "qty_received": 30.0,
                    "batch_no": "DABUR-B1",
                    "warehouse_id": wh.id,
                }
            ]
        },
    )
    assert res_receive.status_code == status.HTTP_200_OK
    assert res_receive.json()["status"] == "received"
    assert res_receive.json()["items"][0]["qty_received"] == 30.0
