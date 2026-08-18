"""
Tests for ProductRepository, ProductService, and Category/Product API endpoints.

Validates DIP compliance, duplicate SKU 409 handling, deactivation guards,
Supabase Storage image uploads, and schema integrity.
"""

from typing import Any

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.core.di import get_storage_service
from app.core.security import CurrentUser, get_current_user, require_permission
from app.db.base import Base
from app.db.session import get_db_session
from app.main import app
from app.models.catalog import Product
from app.models.supplier import POStatusEnum, PurchaseOrder, PurchaseOrderItem, Supplier
from app.repositories.impl.product_repository import InMemoryProductRepository
from app.schemas.products import ProductCreateRequest
from app.services.product_service import ProductService
from app.services.storage_service import MockStorageService


@pytest.fixture
def db_session():
    """Create isolated SQLite database session for product tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


# --- DIP Test: Zero Service Code Changes with In-Memory Fake ---
def test_dip_zero_service_code_changes_with_in_memory_repository() -> None:
    """Proof of Dependency Inversion: ProductService operates identically on in-memory fake."""
    fake_repo = InMemoryProductRepository(
        seed_products=[
            {
                "id": "prod-fake-1",
                "sku": "FAKE-SKU-01",
                "name": "Fake Basmati Rice",
                "wholesale_price": 2000.0,
                "cost_price": 1700.0,
                "reorder_point": 20,
                "reorder_qty": 50,
                "is_active": True,
            }
        ]
    )
    storage_mock = MockStorageService()
    service = ProductService(repository=fake_repo, storage_service=storage_mock)

    # 1. Fetch product
    prod = service.get_product("prod-fake-1")
    assert prod["sku"] == "FAKE-SKU-01"

    # 2. Create new product
    new_prod = service.create_product(
        ProductCreateRequest(
            sku="FAKE-SKU-02",
            name="Fake Wheat Flour",
            wholesale_price=1500.0,
            cost_price=1200.0,
        )
    )
    assert new_prod["sku"] == "FAKE-SKU-02"

    # 3. Duplicate SKU raises 409
    with pytest.raises(HTTPException) as exc_info:
        service.create_product(
            ProductCreateRequest(
                sku="FAKE-SKU-01",
                name="Duplicate Name",
                wholesale_price=100.0,
                cost_price=80.0,
            )
        )
    assert exc_info.value.status_code == 409

    # 4. Open order deactivation block
    fake_repo.set_product_open_orders("prod-fake-1", True)
    with pytest.raises(HTTPException) as exc_info:
        service.deactivate_product("prod-fake-1")
    assert exc_info.value.status_code == 400
    assert "Cannot deactivate product with open" in exc_info.value.detail

    # 5. Image upload
    image_url = service.upload_image(
        product_id="prod-fake-1",
        file_bytes=b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00",
        filename="rice.jpg",
        content_type="image/jpeg",
    )
    assert "product-images" in image_url
    assert fake_repo.get_by_id("prod-fake-1")["image_url"] == image_url


# --- Storage Validation Tests ---
def test_image_upload_validation_file_type_and_size() -> None:
    """Ensure oversized and invalid MIME types are rejected before upload."""
    storage = MockStorageService()

    # Wrong MIME type
    with pytest.raises(HTTPException) as exc_type:
        storage.upload_image(
            file_bytes=b"dummy text",
            original_filename="test.txt",
            content_type="text/plain",
        )
    assert exc_type.value.status_code == 400
    assert "Invalid image type" in exc_type.value.detail

    # Oversized file (> 5 MB)
    oversized_bytes = b"0" * (5 * 1024 * 1024 + 10)
    with pytest.raises(HTTPException) as exc_size:
        storage.upload_image(
            file_bytes=oversized_bytes,
            original_filename="large.png",
            content_type="image/png",
        )
    assert exc_size.value.status_code == 400
    assert "exceeds the maximum allowed limit of 5.00MB" in exc_size.value.detail


# --- FastAPI Endpoints Integration Tests with Database Session ---
def test_products_api_crud_and_validation(db_session: Any) -> None:
    """Full lifecycle testing on PostgreSQL/SQLite session via FastAPI test client."""
    mock_user = CurrentUser(
        id="usr-test-owner",
        email="owner@wareflow.io",
        role="Owner",
        permissions={"inventory:manage", "inventory:view"},
    )

    app.dependency_overrides[get_db_session] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[require_permission("inventory:manage")] = lambda: mock_user
    app.dependency_overrides[get_storage_service] = lambda: MockStorageService()

    client = TestClient(app)

    try:
        # 1. Create category
        cat_resp = client.post("/categories", json={"name": "Grains & Pulses"})
        assert cat_resp.status_code == 201
        cat_id = cat_resp.json()["id"]

        # 2. Create product
        prod_payload = {
            "sku": "RICE-ROYAL-25KG",
            "name": "Royal Basmati Rice 25kg",
            "description": "Export quality long-grain aged rice.",
            "content_details": "100% Traditional Basmati Rice",
            "category_id": cat_id,
            "cost_price": 2100.0,
            "wholesale_price": 2450.0,
            "reorder_point": 15,
            "reorder_qty": 60,
        }
        create_resp = client.post("/products", json=prod_payload)
        assert create_resp.status_code == 201
        prod_data = create_resp.json()
        prod_id = prod_data["id"]
        assert prod_data["sku"] == "RICE-ROYAL-25KG"
        assert prod_data["description"] == "Export quality long-grain aged rice."
        assert prod_data["content_details"] == "100% Traditional Basmati Rice"

        # 3. Duplicate SKU rejection (409 Conflict)
        dup_resp = client.post("/products", json=prod_payload)
        assert dup_resp.status_code == 409
        assert "already exists" in dup_resp.json()["detail"]

        # 4. List products
        list_resp = client.get("/products")
        assert list_resp.status_code == 200
        items = list_resp.json()
        assert any(p["id"] == prod_id for p in items)

        # 5. Filter by category
        cat_filter_resp = client.get(f"/products?category_id={cat_id}")
        assert cat_filter_resp.status_code == 200
        assert len(cat_filter_resp.json()) >= 1

        # 6. Update product
        update_resp = client.patch(
            f"/products/{prod_id}",
            json={"wholesale_price": 2550.0, "description": "Updated aged rice"},
        )
        assert update_resp.status_code == 200
        assert float(update_resp.json()["wholesale_price"]) == 2550.0
        assert update_resp.json()["description"] == "Updated aged rice"

        # 7. Upload Image
        fake_jpeg = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00"
        img_resp = client.post(
            f"/products/{prod_id}/image",
            files={"file": ("product.jpg", fake_jpeg, "image/jpeg")},
        )
        assert img_resp.status_code == 200
        assert "image_url" in img_resp.json()

        # 8. Deactivate product without open orders -> Success
        deact_resp = client.post(f"/products/{prod_id}/deactivate")
        assert deact_resp.status_code == 200
        assert deact_resp.json()["is_active"] is False

    finally:
        app.dependency_overrides.clear()


def test_open_order_blocks_product_deactivation(db_session: Any) -> None:
    """Verify deactivation is blocked when open Purchase Order references product."""
    mock_user = CurrentUser(
        id="usr-test-owner",
        email="owner@wareflow.io",
        role="Owner",
        permissions={"inventory:manage"},
    )
    app.dependency_overrides[get_db_session] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[require_permission("inventory:manage")] = lambda: mock_user

    # Setup Product, Supplier, Open PO
    product = Product(
        sku="OIL-SUN-15L",
        name="Sunflower Cooking Oil 15L",
        cost_price=1600.0,
        wholesale_price=1850.0,
        reorder_point=10,
        reorder_qty=40,
        is_active=True,
    )
    supplier = Supplier(
        name="Golden Harvest Mills",
        gstin="27AABCG1234F1Z5",
        is_active=True,
    )
    db_session.add_all([product, supplier])
    db_session.commit()
    db_session.refresh(product)
    db_session.refresh(supplier)

    po = PurchaseOrder(
        po_number="PO-2026-TEST-001",
        supplier_id=supplier.id,
        status=POStatusEnum.ORDERED,
    )
    db_session.add(po)
    db_session.commit()
    db_session.refresh(po)

    po_item = PurchaseOrderItem(
        po_id=po.id,
        product_id=product.id,
        qty_ordered=50,
        qty_received=0,
        unit_cost=1600.0,
    )
    db_session.add(po_item)
    db_session.commit()

    client = TestClient(app)
    try:
        # Attempt to deactivate product with open PO
        resp = client.post(f"/products/{product.id}/deactivate")
        assert resp.status_code == 400
        assert "Cannot deactivate product with open" in resp.json()["detail"]
    finally:
        app.dependency_overrides.clear()
