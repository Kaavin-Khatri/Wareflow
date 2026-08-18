"""Automated unit and integration tests for Supplier CRUD (Step 7.1)."""

from datetime import date

import pytest
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.api.routers import suppliers as suppliers_router
from app.core.di import get_supplier_service
from app.core.security import CurrentUser, get_current_user, require_permission
from app.db.base import Base
from app.models.supplier import Supplier
from app.repositories.impl.supplier_repository import (
    InMemorySupplierRepository,
    SqlAlchemySupplierRepository,
)
from app.schemas.suppliers import SupplierCreateRequest, SupplierUpdateRequest
from app.services.supplier_service import SupplierService


@pytest.fixture
def supplier_db():
    """Create in-memory SQLite database for Supplier testing."""
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
        id="supplier-admin-1",
        email="admin@wareflow.io",
        role="Manager",
        permissions={"inventory:view", "inventory:manage"},
    )


# ---------------------------------------------------------------------------
# Unit Tests (InMemory & Service Domain Rules)
# ---------------------------------------------------------------------------


def test_supplier_crud_in_memory():
    """Test SupplierService with InMemorySupplierRepository (DIP verification)."""
    repo = InMemorySupplierRepository()
    service = SupplierService(repository=repo)

    # 1. Create
    payload = SupplierCreateRequest(
        name="Hindustan Unilever Ltd",
        contact_person="Rajesh Sharma",
        phone="+919876543210",
        email="rajesh@hul.com",
        address="Bandra East, Mumbai, MH",
        gstin="27AAACH1234F1Z5",
        fssai_license_no="10012022000123",
        fssai_expiry_date=date(2028, 12, 31),
        is_active=True,
    )
    created = service.create_supplier(payload, actor_id="admin-1")
    assert created.id is not None
    assert created.name == "Hindustan Unilever Ltd"
    assert created.gstin == "27AAACH1234F1Z5"

    # 2. Get
    fetched = service.get_supplier(created.id)
    assert fetched.name == "Hindustan Unilever Ltd"
    assert fetched.contact_person == "Rajesh Sharma"

    # 3. List
    items = service.list_suppliers(search="Unilever")
    assert len(items) == 1
    assert items[0].id == created.id

    # 4. Update
    update_payload = SupplierUpdateRequest(
        contact_person="Vikram Malhotra",
        phone="+919123456780",
    )
    updated = service.update_supplier(created.id, update_payload, actor_id="admin-1")
    assert updated.contact_person == "Vikram Malhotra"
    assert updated.phone == "+919123456780"


def test_supplier_duplicate_name_blocked():
    """Verify duplicate supplier names (case-insensitive) are blocked with 409 Conflict."""
    repo = InMemorySupplierRepository()
    service = SupplierService(repository=repo)

    payload = SupplierCreateRequest(
        name="ITC Limited",
        gstin="19AAACI1681G1Z0",
    )
    service.create_supplier(payload)

    # Attempt duplicate with different casing and whitespace
    duplicate_payload = SupplierCreateRequest(
        name="  itc limited  ",
        gstin="19AAACI1681G1Z0",
    )
    with pytest.raises(HTTPException) as exc_info:
        service.create_supplier(duplicate_payload)

    assert exc_info.value.status_code == status.HTTP_409_CONFLICT
    assert "already exists" in exc_info.value.detail


def test_supplier_gstin_format_validation():
    """Verify standard Indian GSTIN 15-character format enforcement."""
    repo = InMemorySupplierRepository()
    service = SupplierService(repository=repo)

    # Invalid GSTIN (too short)
    with pytest.raises(HTTPException) as exc_info:
        service.create_supplier(SupplierCreateRequest(name="Vendor A", gstin="INVALID123"))
    assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "Invalid GSTIN format" in exc_info.value.detail

    # Valid GSTIN
    valid_supplier = service.create_supplier(
        SupplierCreateRequest(name="Vendor B", gstin="29AABCU9603R1Z2")
    )
    assert valid_supplier.gstin == "29AABCU9603R1Z2"


def test_supplier_contact_validation():
    """Verify email and phone validation in SupplierService."""
    repo = InMemorySupplierRepository()
    service = SupplierService(repository=repo)

    # Invalid email
    with pytest.raises(HTTPException) as exc_info:
        service.create_supplier(
            SupplierCreateRequest(name="Vendor C", email="invalid-email-address")
        )
    assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "Invalid email address format" in exc_info.value.detail

    # Invalid phone (< 7 digits)
    with pytest.raises(HTTPException) as exc_info_phone:
        service.create_supplier(SupplierCreateRequest(name="Vendor D", phone="123"))
    assert exc_info_phone.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "Invalid phone number" in exc_info_phone.value.detail


# ---------------------------------------------------------------------------
# Integration Tests (SqlAlchemy & FastAPI REST endpoints)
# ---------------------------------------------------------------------------


def test_supplier_sqlalchemy_crud(supplier_db):
    """Test SqlAlchemySupplierRepository with real database session."""
    repo = SqlAlchemySupplierRepository(session=supplier_db)
    service = SupplierService(repository=repo)

    # 1. Create supplier
    created = service.create_supplier(
        SupplierCreateRequest(
            name="Nestle India Ltd",
            contact_person="Sunil Varma",
            phone="+919876500000",
            email="sunil@nestle.in",
            gstin="07AAACN1234N1Z1",
            fssai_license_no="10014011000555",
            is_active=True,
        )
    )
    assert created.id is not None
    assert created.name == "Nestle India Ltd"

    # 2. Fetch from DB
    db_supplier = supplier_db.get(Supplier, created.id)
    assert db_supplier is not None
    assert db_supplier.gstin == "07AAACN1234N1Z1"

    # 3. Update active status
    updated = service.update_supplier(
        created.id,
        SupplierUpdateRequest(is_active=False),
    )
    assert updated.is_active is False

    # 4. Filter active vs inactive
    active_list = service.list_suppliers(is_active=True)
    assert len(active_list) == 0

    inactive_list = service.list_suppliers(is_active=False)
    assert len(inactive_list) == 1


def test_supplier_api_endpoints(supplier_db, mock_user):
    """Integration test for FastAPI /suppliers endpoints."""
    app = FastAPI()
    app.include_router(suppliers_router.router)

    repo = SqlAlchemySupplierRepository(session=supplier_db)
    service = SupplierService(repository=repo)

    app.dependency_overrides[get_supplier_service] = lambda: service
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[require_permission("inventory:manage")] = lambda: mock_user

    client = TestClient(app)

    # 1. Create Supplier (POST /suppliers)
    create_res = client.post(
        "/suppliers",
        json={
            "name": "Tata Consumer Products",
            "contact_person": "Priya Sen",
            "phone": "+919845012345",
            "email": "priya@tataconsumer.com",
            "address": "Kolkata, West Bengal",
            "gstin": "19AAACT1234C1Z9",
            "is_active": True,
        },
    )
    assert create_res.status_code == status.HTTP_201_CREATED
    sup_data = create_res.json()
    assert sup_data["name"] == "Tata Consumer Products"
    assert sup_data["gstin"] == "19AAACT1234C1Z9"
    supplier_id = sup_data["id"]

    # 2. Get Supplier (GET /suppliers/{id})
    get_res = client.get(f"/suppliers/{supplier_id}")
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.json()["contact_person"] == "Priya Sen"

    # 3. List Suppliers (GET /suppliers?search=Tata)
    list_res = client.get("/suppliers?search=Tata")
    assert list_res.status_code == status.HTTP_200_OK
    assert len(list_res.json()) == 1

    # 4. Patch Supplier (PATCH /suppliers/{id})
    patch_res = client.patch(
        f"/suppliers/{supplier_id}",
        json={"contact_person": "Amit Roy", "phone": "+919845099999"},
    )
    assert patch_res.status_code == status.HTTP_200_OK
    assert patch_res.json()["contact_person"] == "Amit Roy"
    assert patch_res.json()["phone"] == "+919845099999"

    # 5. Non-existent supplier (GET /suppliers/non-existent-id -> 404)
    missing_res = client.get("/suppliers/00000000-0000-0000-0000-000000000000")
    assert missing_res.status_code == status.HTTP_404_NOT_FOUND
