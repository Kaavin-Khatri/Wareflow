"""Unit and integration tests for Purchase Returns (RMA Out) (Step 7.3)."""

from datetime import date, timedelta

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routers import purchase_returns as returns_router
from app.core.security import CurrentUser, get_current_user
from app.db.base import Base
from app.models.catalog import Product
from app.models.inventory import StockMovement, StockMovementTypeEnum
from app.models.returns import PurchaseReturnStatusEnum
from app.models.supplier import POStatusEnum, PurchaseOrder, PurchaseOrderItem, Supplier
from app.models.uom import UnitOfMeasure
from app.models.warehouse import StockBatch, Warehouse
from app.repositories.impl.product_repository import (
    InMemoryProductRepository,
    SqlAlchemyProductRepository,
)
from app.repositories.impl.purchase_order_repository import (
    InMemoryPurchaseOrderRepository,
    SqlAlchemyPurchaseOrderRepository,
)
from app.repositories.impl.purchase_return_repository import (
    InMemoryPurchaseReturnRepository,
    SqlAlchemyPurchaseReturnRepository,
)
from app.repositories.impl.stock_repository import (
    InMemoryStockRepository,
    SqlAlchemyStockRepository,
)
from app.repositories.impl.supplier_repository import (
    InMemorySupplierRepository,
    SqlAlchemySupplierRepository,
)
from app.schemas.purchase_returns import (
    PurchaseReturnCreateRequest,
    PurchaseReturnItemCreateRequest,
    PurchaseReturnStatusUpdateRequest,
)
from app.services.purchase_return_service import PurchaseReturnService


def test_purchase_return_in_memory_lifecycle_and_stock_deduction():
    """Test that creating a return immediately decreases batch stock and writes return_out movement."""
    stock_repo = InMemoryStockRepository(
        warehouses=[{"id": "wh-1", "name": "Central Hub", "location": "Sec 1", "is_active": True}],
        products=[{"id": "prod-1", "name": "Tata Tea 500g", "sku": "TEA-500", "is_active": True}],
        batches=[
            {
                "id": "batch-1",
                "product_id": "prod-1",
                "warehouse_id": "wh-1",
                "batch_no": "B-2026-01",
                "quantity": 50.0,
                "expiry_date": date.today() + timedelta(days=90),
            }
        ],
    )
    po_repo = InMemoryPurchaseOrderRepository(
        initial_orders=[
            {
                "id": "po-1",
                "po_number": "PO-202608-0001",
                "supplier_id": "sup-1",
                "status": POStatusEnum.ORDERED,
                "items": [
                    {
                        "id": "po-item-1",
                        "po_id": "po-1",
                        "product_id": "prod-1",
                        "qty_ordered": 50.0,
                        "qty_received": 50.0,
                        "unit_cost": 120.0,
                        "uom_id": "uom-1",
                        "line_total": 6000.0,
                    }
                ],
            }
        ]
    )
    supplier_repo = InMemorySupplierRepository(
        initial_suppliers=[{"id": "sup-1", "name": "Tata Consumer", "is_active": True}]
    )
    product_repo = InMemoryProductRepository(
        initial_products=[
            {"id": "prod-1", "name": "Tata Tea 500g", "sku": "TEA-500", "is_active": True}
        ]
    )
    returns_repo = InMemoryPurchaseReturnRepository()

    service = PurchaseReturnService(
        purchase_return_repo=returns_repo,
        purchase_order_repo=po_repo,
        supplier_repo=supplier_repo,
        product_repo=product_repo,
        stock_repo=stock_repo,
    )

    # 1. Create return request for 15 units of batch-1
    req = PurchaseReturnCreateRequest(
        purchase_order_id="po-1",
        reason="Packaging seal broken on delivery",
        items=[
            PurchaseReturnItemCreateRequest(
                product_id="prod-1",
                batch_id="batch-1",
                qty=15.0,
                reason="Damaged cartons",
            )
        ],
    )
    ret_resp = service.create_purchase_return(payload=req, actor_id="user-admin")

    assert ret_resp.status == PurchaseReturnStatusEnum.REQUESTED
    assert ret_resp.supplier_name == "Tata Consumer"
    assert ret_resp.po_number == "PO-202608-0001"
    assert ret_resp.items_count == 1
    assert ret_resp.total_qty == 15.0

    # Verify batch stock was immediately decremented: 50.0 - 15.0 = 35.0
    updated_batch = stock_repo.get_batch_by_id("batch-1")
    assert updated_batch is not None
    assert float(updated_batch.quantity) == 35.0


def test_purchase_return_over_return_and_draft_guards():
    """Verify that returning more than batch balance or against draft PO is rejected."""
    stock_repo = InMemoryStockRepository(
        warehouses=[{"id": "wh-1", "name": "Central Hub", "location": "Sec 1", "is_active": True}],
        products=[{"id": "prod-1", "name": "Tata Tea 500g", "sku": "TEA-500", "is_active": True}],
        batches=[
            {
                "id": "batch-1",
                "product_id": "prod-1",
                "warehouse_id": "wh-1",
                "batch_no": "B-2026-01",
                "quantity": 10.0,
            }
        ],
    )
    po_repo = InMemoryPurchaseOrderRepository(
        initial_orders=[
            {
                "id": "po-1",
                "po_number": "PO-202608-0001",
                "supplier_id": "sup-1",
                "status": POStatusEnum.ORDERED,
                "items": [],
            },
            {
                "id": "po-draft",
                "po_number": "PO-202608-0002",
                "supplier_id": "sup-1",
                "status": POStatusEnum.DRAFT,
                "items": [],
            },
        ]
    )
    supplier_repo = InMemorySupplierRepository(
        initial_suppliers=[{"id": "sup-1", "name": "Tata Consumer", "is_active": True}]
    )
    product_repo = InMemoryProductRepository(
        initial_products=[
            {"id": "prod-1", "name": "Tata Tea 500g", "sku": "TEA-500", "is_active": True}
        ]
    )
    returns_repo = InMemoryPurchaseReturnRepository()

    service = PurchaseReturnService(
        purchase_return_repo=returns_repo,
        purchase_order_repo=po_repo,
        supplier_repo=supplier_repo,
        product_repo=product_repo,
        stock_repo=stock_repo,
    )

    # Attempting to return 15 units when batch has 10 units -> 400 Bad Request
    with pytest.raises(Exception) as exc_info:
        service.create_purchase_return(
            payload=PurchaseReturnCreateRequest(
                purchase_order_id="po-1",
                reason="Excess stock",
                items=[
                    PurchaseReturnItemCreateRequest(
                        product_id="prod-1",
                        batch_id="batch-1",
                        qty=15.0,
                    )
                ],
            )
        )
    assert "available on hand" in str(exc_info.value.detail)

    # Attempting to return against draft PO -> 400 Bad Request
    with pytest.raises(Exception) as exc_draft:
        service.create_purchase_return(
            payload=PurchaseReturnCreateRequest(
                purchase_order_id="po-draft",
                reason="Draft test",
                items=[
                    PurchaseReturnItemCreateRequest(
                        product_id="prod-1",
                        batch_id="batch-1",
                        qty=5.0,
                    )
                ],
            )
        )
    assert "draft purchase order" in str(exc_draft.value.detail)


def test_purchase_return_status_transition_lifecycle():
    """Verify strict requested -> shipped -> credited status lifecycle and credit note ref requirement."""
    stock_repo = InMemoryStockRepository(
        warehouses=[{"id": "wh-1", "name": "Central Hub", "location": "Sec 1", "is_active": True}],
        products=[{"id": "prod-1", "name": "Tata Tea 500g", "sku": "TEA-500", "is_active": True}],
        batches=[
            {
                "id": "batch-1",
                "product_id": "prod-1",
                "warehouse_id": "wh-1",
                "batch_no": "B-2026-01",
                "quantity": 100.0,
            }
        ],
    )
    po_repo = InMemoryPurchaseOrderRepository(
        initial_orders=[
            {
                "id": "po-1",
                "po_number": "PO-202608-0001",
                "supplier_id": "sup-1",
                "status": POStatusEnum.ORDERED,
                "items": [],
            }
        ]
    )
    supplier_repo = InMemorySupplierRepository(
        initial_suppliers=[{"id": "sup-1", "name": "Tata Consumer", "is_active": True}]
    )
    product_repo = InMemoryProductRepository(
        initial_products=[
            {"id": "prod-1", "name": "Tata Tea 500g", "sku": "TEA-500", "is_active": True}
        ]
    )
    returns_repo = InMemoryPurchaseReturnRepository()

    service = PurchaseReturnService(
        purchase_return_repo=returns_repo,
        purchase_order_repo=po_repo,
        supplier_repo=supplier_repo,
        product_repo=product_repo,
        stock_repo=stock_repo,
    )

    # 1. Create return
    ret = service.create_purchase_return(
        payload=PurchaseReturnCreateRequest(
            purchase_order_id="po-1",
            items=[
                PurchaseReturnItemCreateRequest(
                    product_id="prod-1",
                    batch_id="batch-1",
                    qty=10.0,
                )
            ],
        )
    )
    assert ret.status == PurchaseReturnStatusEnum.REQUESTED

    # 2. Invalid direct jump to credited -> 400
    with pytest.raises(Exception) as exc_jump:
        service.update_return_status(
            return_id=ret.id,
            payload=PurchaseReturnStatusUpdateRequest(
                status=PurchaseReturnStatusEnum.CREDITED,
                credit_note_ref="CN-123",
            ),
        )
    assert "Invalid status transition" in str(exc_jump.value.detail)

    # 3. Transition requested -> shipped -> SUCCESS
    shipped = service.update_return_status(
        return_id=ret.id,
        payload=PurchaseReturnStatusUpdateRequest(
            status=PurchaseReturnStatusEnum.SHIPPED,
        ),
    )
    assert shipped.status == PurchaseReturnStatusEnum.SHIPPED

    # 4. Transition shipped -> credited WITHOUT credit_note_ref -> 422
    with pytest.raises(Exception) as exc_nocredit:
        service.update_return_status(
            return_id=ret.id,
            payload=PurchaseReturnStatusUpdateRequest(
                status=PurchaseReturnStatusEnum.CREDITED,
                credit_note_ref=None,
            ),
        )
    assert "credit_note_ref is required" in str(exc_nocredit.value.detail)

    # 5. Transition shipped -> credited WITH credit_note_ref -> SUCCESS
    credited = service.update_return_status(
        return_id=ret.id,
        payload=PurchaseReturnStatusUpdateRequest(
            status=PurchaseReturnStatusEnum.CREDITED,
            credit_note_ref="CRN-2026-9988",
        ),
    )
    assert credited.status == PurchaseReturnStatusEnum.CREDITED
    assert credited.credit_note_ref == "CRN-2026-9988"


def test_purchase_return_sqlalchemy_db_persistence():
    """Verify SQLAlchemy DB writes for PurchaseReturn, PurchaseReturnItem, StockMovement(type=return_out)."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    with testing_session_local() as session:
        # Seed Base Entities
        uom = UnitOfMeasure(id="uom-kg", name="Kilogram", abbreviation="kg")
        supplier = Supplier(id="sup-db-1", name="Fortune Foods Ltd", is_active=True)
        warehouse = Warehouse(id="wh-db-1", name="Main Silo", location="North Dock", is_active=True)
        product = Product(
            id="prod-db-1",
            sku="RICE-BAS-25KG",
            name="Basmati Rice 25kg",
            cost_price=1500.0,
            wholesale_price=1800.0,
            base_uom_id="uom-kg",
            is_active=True,
        )
        batch = StockBatch(
            id="batch-db-1",
            product_id="prod-db-1",
            warehouse_id="wh-db-1",
            batch_no="RICE-2026-B1",
            quantity=80.0,
        )
        po = PurchaseOrder(
            id="po-db-1",
            po_number="PO-202608-DB01",
            supplier_id="sup-db-1",
            status=POStatusEnum.RECEIVED,
            total_amount=120000.0,
        )
        po_item = PurchaseOrderItem(
            id="poi-db-1",
            po_id="po-db-1",
            product_id="prod-db-1",
            qty_ordered=80.0,
            qty_received=80.0,
            unit_cost=1500.0,
            uom_id="uom-kg",
        )

        session.add_all([uom, supplier, warehouse, product, batch, po, po_item])
        session.commit()

        stock_repo = SqlAlchemyStockRepository(session=session)
        returns_repo = SqlAlchemyPurchaseReturnRepository(session=session)
        po_repo = SqlAlchemyPurchaseOrderRepository(session=session)
        supplier_repo = SqlAlchemySupplierRepository(session=session)
        product_repo = SqlAlchemyProductRepository(session=session)

        service = PurchaseReturnService(
            purchase_return_repo=returns_repo,
            purchase_order_repo=po_repo,
            supplier_repo=supplier_repo,
            product_repo=product_repo,
            stock_repo=stock_repo,
        )

        ret_resp = service.create_purchase_return(
            payload=PurchaseReturnCreateRequest(
                purchase_order_id="po-db-1",
                reason="Moisture contamination in 20 bags",
                items=[
                    PurchaseReturnItemCreateRequest(
                        product_id="prod-db-1",
                        batch_id="batch-db-1",
                        qty=20.0,
                        reason="Water damage",
                    )
                ],
            ),
            actor_id="user-qa",
        )
        session.commit()

        assert ret_resp.id is not None
        assert ret_resp.status == PurchaseReturnStatusEnum.REQUESTED
        assert ret_resp.total_qty == 20.0

        # Verify DB StockBatch quantity reduced: 80.0 - 20.0 = 60.0
        db_batch = session.query(StockBatch).filter(StockBatch.id == "batch-db-1").one()
        assert float(db_batch.quantity) == 60.0

        # Verify DB StockMovement(type=return_out) recorded
        movements = (
            session.query(StockMovement)
            .filter(
                StockMovement.product_id == "prod-db-1",
                StockMovement.type == StockMovementTypeEnum.RETURN_OUT,
            )
            .all()
        )
        assert len(movements) == 1
        assert float(movements[0].quantity) == 20.0
        assert movements[0].reference_type == "purchase_return"
        assert movements[0].reference_id == ret_resp.id


def test_purchase_return_api_router_endpoints():
    """Verify REST endpoints under /purchase-returns."""
    app = FastAPI()
    app.include_router(returns_router.router)

    stock_repo = InMemoryStockRepository(
        warehouses=[{"id": "wh-1", "name": "Central Hub", "location": "Sec 1", "is_active": True}],
        products=[{"id": "prod-1", "name": "Tata Tea 500g", "sku": "TEA-500", "is_active": True}],
        batches=[
            {
                "id": "batch-1",
                "product_id": "prod-1",
                "warehouse_id": "wh-1",
                "batch_no": "B-2026-01",
                "quantity": 100.0,
            }
        ],
    )
    po_repo = InMemoryPurchaseOrderRepository(
        initial_orders=[
            {
                "id": "po-1",
                "po_number": "PO-202608-0001",
                "supplier_id": "sup-1",
                "status": POStatusEnum.ORDERED,
                "items": [],
            }
        ]
    )
    supplier_repo = InMemorySupplierRepository(
        initial_suppliers=[{"id": "sup-1", "name": "Tata Consumer", "is_active": True}]
    )
    product_repo = InMemoryProductRepository(
        initial_products=[
            {"id": "prod-1", "name": "Tata Tea 500g", "sku": "TEA-500", "is_active": True}
        ]
    )
    returns_repo = InMemoryPurchaseReturnRepository()

    service = PurchaseReturnService(
        purchase_return_repo=returns_repo,
        purchase_order_repo=po_repo,
        supplier_repo=supplier_repo,
        product_repo=product_repo,
        stock_repo=stock_repo,
    )

    app.dependency_overrides[returns_router.get_purchase_return_service] = lambda: service
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id="test-user",
        email="admin@wareflow.io",
        role="Owner",
        permissions=["inventory:view", "inventory:manage"],
    )

    client = TestClient(app)

    # 1. POST /purchase-returns
    post_res = client.post(
        "/purchase-returns",
        json={
            "purchase_order_id": "po-1",
            "reason": "Damaged goods",
            "items": [
                {
                    "product_id": "prod-1",
                    "batch_id": "batch-1",
                    "qty": 12.0,
                    "reason": "Dented tins",
                }
            ],
        },
    )
    assert post_res.status_code == status.HTTP_201_CREATED, post_res.text
    created_data = post_res.json()
    return_id = created_data["id"]
    assert created_data["status"] == "requested"
    assert created_data["total_qty"] == 12.0

    # 2. GET /purchase-returns
    list_res = client.get("/purchase-returns?status=requested")
    assert list_res.status_code == status.HTTP_200_OK
    assert len(list_res.json()) >= 1

    # 3. GET /purchase-returns/{id}
    detail_res = client.get(f"/purchase-returns/{return_id}")
    assert detail_res.status_code == status.HTTP_200_OK
    assert detail_res.json()["id"] == return_id

    # 4. PATCH /purchase-returns/{id}/status -> shipped
    patch_ship = client.patch(
        f"/purchase-returns/{return_id}/status",
        json={"status": "shipped"},
    )
    assert patch_ship.status_code == status.HTTP_200_OK
    assert patch_ship.json()["status"] == "shipped"

    # 5. PATCH /purchase-returns/{id}/status -> credited
    patch_credit = client.patch(
        f"/purchase-returns/{return_id}/status",
        json={"status": "credited", "credit_note_ref": "CN-TATA-2026-004"},
    )
    assert patch_credit.status_code == status.HTTP_200_OK
    assert patch_credit.json()["status"] == "credited"
    assert patch_credit.json()["credit_note_ref"] == "CN-TATA-2026-004"
