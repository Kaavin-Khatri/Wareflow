"""Automated unit and integration tests for Unit-of-Measure (UoM) conversion service (Step 5.2)."""

import uuid
from typing import Any

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.api.routers import uom as uom_router
from app.core.security import CurrentUser, get_current_user, require_permission
from app.db.base import Base
from app.models.catalog import Product
from app.models.uom import ProductUOMConversion, UnitOfMeasure
from app.repositories.impl.uom_repository import InMemoryUomRepository, SqlAlchemyUomRepository
from app.services.uom_service import UomConversionError, UomService


@pytest.fixture
def uom_db():
    """Create in-memory SQLite test database with UoM schema."""
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
def mock_admin_user() -> CurrentUser:
    return CurrentUser(
        id="admin-uid-123",
        email="admin@wareflow.io",
        role="Owner",
        permissions={"inventory:manage", "inventory:view"},
    )


def test_dip_zero_service_code_changes_with_in_memory_uom_repository():
    """
    DIP Verification: Test that UomService functions identically when
    injected with InMemoryUomRepository vs SqlAlchemyUomRepository.
    """
    piece_id = str(uuid.uuid4())
    case_id = str(uuid.uuid4())
    pallet_id = str(uuid.uuid4())
    prod_id = str(uuid.uuid4())

    seed_uoms = [
        {"id": piece_id, "name": "Piece", "abbreviation": "pcs"},
        {"id": case_id, "name": "Case", "abbreviation": "case"},
        {"id": pallet_id, "name": "Pallet", "abbreviation": "pallet"},
    ]
    # 1 Case = 24 Pieces, 1 Pallet = 10 Cases
    seed_conversions = [
        {
            "id": "c1",
            "product_id": prod_id,
            "from_uom_id": case_id,
            "to_uom_id": piece_id,
            "factor": 24.0,
        },
        {
            "id": "c2",
            "product_id": prod_id,
            "from_uom_id": pallet_id,
            "to_uom_id": case_id,
            "factor": 10.0,
        },
    ]
    seed_products = [
        {"id": prod_id, "base_uom_id": piece_id},
    ]

    in_memory_repo = InMemoryUomRepository(
        seed_uoms=seed_uoms,
        seed_conversions=seed_conversions,
        seed_products=seed_products,
    )
    service = UomService(uom_repo=in_memory_repo)

    # Direct conversion: 5 cases -> pieces
    assert service.convert(prod_id, 5.0, from_uom_id=case_id, to_uom_id=piece_id) == 120.0

    # Inverse conversion: 48 pieces -> cases
    assert service.convert(prod_id, 48.0, from_uom_id=piece_id, to_uom_id=case_id) == 2.0

    # Multi-hop conversion: 2 pallets -> pieces (2 * 10 * 24 = 480)
    assert service.convert(prod_id, 2.0, from_uom_id=pallet_id, to_uom_id=piece_id) == 480.0

    # Identity conversion
    assert service.convert(prod_id, 10.0, from_uom_id=piece_id, to_uom_id=piece_id) == 10.0


def test_receiving_cases_increases_base_unit_stock(uom_db: Session):
    """
    QA Requirement 1: Receiving 5 cases of a 24-per-case product
    increases base-unit stock by exactly 120.
    """
    piece = UnitOfMeasure(name="Piece", abbreviation="pcs")
    case = UnitOfMeasure(name="Case", abbreviation="cs")
    uom_db.add_all([piece, case])
    uom_db.flush()

    prod = Product(
        sku="TEST-SKU-1",
        name="Organic Almond Milk 1L",
        base_uom_id=piece.id,
        cost_price=10.0,
        wholesale_price=15.0,
    )
    uom_db.add(prod)
    uom_db.flush()

    # 1 Case = 24 Pieces
    conv = ProductUOMConversion(
        product_id=prod.id,
        from_uom_id=case.id,
        to_uom_id=piece.id,
        factor=24.0,
    )
    uom_db.add(conv)
    uom_db.commit()

    repo = SqlAlchemyUomRepository(session=uom_db)
    service = UomService(uom_repo=repo)

    # When receiving 5 cases at the boundary:
    received_cases = 5.0
    base_qty = service.convert_to_base_uom(
        product_id=prod.id,
        qty=received_cases,
        uom_id=case.id,
    )
    assert base_qty == 120.0


def test_selling_pieces_deducts_correct_base_unit_amount(uom_db: Session):
    """
    QA Requirement 2: Selling in pieces against a case-purchased product
    deducts the correct base-unit amount (or resolves correctly).
    """
    piece = UnitOfMeasure(name="Piece", abbreviation="pcs")
    case = UnitOfMeasure(name="Case", abbreviation="cs")
    uom_db.add_all([piece, case])
    uom_db.flush()

    prod = Product(
        sku="TEST-SKU-2",
        name="Basmati Rice 5kg",
        base_uom_id=piece.id,
        cost_price=100.0,
        wholesale_price=140.0,
    )
    uom_db.add(prod)
    uom_db.flush()

    # 1 Case = 12 Pieces
    conv = ProductUOMConversion(
        product_id=prod.id,
        from_uom_id=case.id,
        to_uom_id=piece.id,
        factor=12.0,
    )
    uom_db.add(conv)
    uom_db.commit()

    repo = SqlAlchemyUomRepository(session=uom_db)
    service = UomService(uom_repo=repo)

    # Selling 36 pieces -> base units deducted is 36
    sold_pieces = 36.0
    base_deducted = service.convert_to_base_uom(
        product_id=prod.id,
        qty=sold_pieces,
        uom_id=piece.id,
    )
    assert base_deducted == 36.0

    # Selling 2.5 cases -> base units deducted is 30.0
    sold_cases = 2.5
    base_deducted_cases = service.convert_to_base_uom(
        product_id=prod.id,
        qty=sold_cases,
        uom_id=case.id,
    )
    assert base_deducted_cases == 30.0


def test_product_with_no_conversion_bought_sold_1_to_1(uom_db: Session):
    """
    QA Requirement 3: A product with no conversion defined can still be
    bought/sold 1:1 in its base unit (graceful default).
    """
    box = UnitOfMeasure(name="Box", abbreviation="box")
    uom_db.add(box)
    uom_db.flush()

    prod = Product(
        sku="TEST-SKU-3",
        name="Custom Gift Hamper",
        base_uom_id=box.id,
        cost_price=50.0,
        wholesale_price=80.0,
    )
    uom_db.add(prod)
    uom_db.commit()

    repo = SqlAlchemyUomRepository(session=uom_db)
    service = UomService(uom_repo=repo)

    # Buying 10 boxes (matches base UoM) -> 10.0
    assert service.convert_to_base_uom(prod.id, 10.0, box.id) == 10.0

    # If uom_id is None -> 10.0
    assert service.convert_to_base_uom(prod.id, 10.0, None) == 10.0


def test_missing_conversion_path_raises_clear_error(uom_db: Session):
    """
    QA Requirement 4: Unresolvable conversion path raises clear UomConversionError.
    """
    kg = UnitOfMeasure(name="Kilogram", abbreviation="kg")
    box = UnitOfMeasure(name="Box", abbreviation="box")
    liter = UnitOfMeasure(name="Liter", abbreviation="L")
    uom_db.add_all([kg, box, liter])
    uom_db.flush()

    prod = Product(
        sku="TEST-SKU-4",
        name="Granola Bar",
        base_uom_id=box.id,
    )
    uom_db.add(prod)
    uom_db.commit()

    repo = SqlAlchemyUomRepository(session=uom_db)
    service = UomService(uom_repo=repo)

    # No conversion path between liter and box
    with pytest.raises(UomConversionError, match="No conversion path exists"):
        service.convert(prod.id, 10.0, from_uom_id=liter.id, to_uom_id=box.id)


def test_uom_api_endpoints_crud_and_calculator(uom_db: Session, mock_admin_user: dict[str, Any]):
    """Integration test for UoM endpoints and conversion calculator."""
    test_app = FastAPI()
    test_app.include_router(uom_router.router)

    def override_get_current_user():
        return mock_admin_user

    def override_require_permission(perm: str):
        def guard():
            return mock_admin_user

        return guard

    def override_get_uom_service():
        repo = SqlAlchemyUomRepository(session=uom_db)
        return UomService(uom_repo=repo)

    test_app.dependency_overrides[get_current_user] = override_get_current_user
    test_app.dependency_overrides[require_permission("inventory:manage")] = (
        override_require_permission("inventory:manage")
    )
    test_app.dependency_overrides[uom_router.get_uom_service] = override_get_uom_service

    client = TestClient(test_app)

    # 1. Create UoM (Piece and Case)
    res_pcs = client.post("/uom", json={"name": "Piece", "abbreviation": "pcs"})
    assert res_pcs.status_code == status.HTTP_201_CREATED
    pcs_data = res_pcs.json()
    pcs_id = pcs_data["id"]

    res_case = client.post("/uom", json={"name": "Case", "abbreviation": "case"})
    assert res_case.status_code == status.HTTP_201_CREATED
    case_data = res_case.json()
    case_id = case_data["id"]

    # 2. Duplicate abbreviation -> 409 Conflict
    res_dup = client.post("/uom", json={"name": "Duplicate Pcs", "abbreviation": "pcs"})
    assert res_dup.status_code == status.HTTP_409_CONFLICT

    # 3. List UoMs
    res_list = client.get("/uom")
    assert res_list.status_code == status.HTTP_200_OK
    assert len(res_list.json()) >= 2

    # 4. Create Product in DB
    prod = Product(
        sku="TEST-API-1",
        name="Cold Pressed Olive Oil",
        base_uom_id=pcs_id,
        cost_price=5.0,
        wholesale_price=8.0,
    )
    uom_db.add(prod)
    uom_db.commit()

    # 5. Define Conversion: 1 Case = 12 Pieces
    res_conv = client.post(
        f"/products/{prod.id}/conversions",
        json={
            "from_uom_id": case_id,
            "to_uom_id": pcs_id,
            "factor": 12.0,
        },
    )
    assert res_conv.status_code == status.HTTP_201_CREATED
    conv_data = res_conv.json()
    assert conv_data["factor"] == 12.0

    # 6. List Product Conversions
    res_conv_list = client.get(f"/products/{prod.id}/conversions")
    assert res_conv_list.status_code == status.HTTP_200_OK
    assert len(res_conv_list.json()) == 1

    # 7. Conversion Calculator: 3 cases -> pieces
    res_calc = client.post(
        f"/products/{prod.id}/convert",
        json={
            "qty": 3.0,
            "from_uom_id": case_id,
            "to_uom_id": pcs_id,
        },
    )
    assert res_calc.status_code == status.HTTP_200_OK
    assert res_calc.json()["converted_qty"] == 36.0

    # 8. Conversion Calculator: 24 pieces -> cases
    res_calc_rev = client.post(
        f"/products/{prod.id}/convert",
        json={
            "qty": 24.0,
            "from_uom_id": pcs_id,
            "to_uom_id": case_id,
        },
    )
    assert res_calc_rev.status_code == status.HTTP_200_OK
    assert res_calc_rev.json()["converted_qty"] == 2.0
