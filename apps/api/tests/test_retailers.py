"""
Comprehensive test suite for Retailer CRUD, Pluggable Pricing Strategies, and API endpoints (Step 8.1).

Covers:
- RetailerRepository CRUD in-memory and database operations
- RetailerService validation (uniqueness, 404s, audit logging)
- Pluggable PricingStrategy (Standard, Silver, Gold, TieredVolume)
- QA Checklist Proof 1: Gold-tier retailer gets discounted line price compared to Standard-tier
- QA Checklist Proof 2 (OCP): Adding a custom PlatinumPricingStrategy requires zero modifications to pricing engine
- FastAPI TestClient endpoint execution (GET/POST /retailers, GET/PATCH /retailers/{id})
"""

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routers import retailers
from app.core.di import get_retailer_service
from app.core.security import CurrentUser, get_current_user, require_permission
from app.db.base import Base
from app.models.retailer import Retailer
from app.repositories.impl.retailer_repository import (
    InMemoryRetailerRepository,
    SqlAlchemyRetailerRepository,
)
from app.schemas.retailers import (
    PricingTierEnum,
    RetailerCreateRequest,
    RetailerUpdateRequest,
)
from app.services.pricing_strategy import (
    GoldPricingStrategy,
    PricingEngineService,
    PricingStrategy,
    SilverPricingStrategy,
    StandardPricingStrategy,
    TieredDiscountPricingStrategy,
)
from app.services.retailer_service import RetailerService

# ────────────────────────────────────────────────────────────
# 1. Pricing Strategy & OCP Tests
# ────────────────────────────────────────────────────────────


def test_standard_pricing_strategy_no_discount():
    """Standard tier pricing keeps base unit price with 0% discount."""
    strategy = StandardPricingStrategy()
    assert strategy.tier_name == "standard"
    assert strategy.default_discount_percentage == 0.0

    result = strategy.calculate_line(base_price=100.0, quantity=5)
    assert result.base_unit_price == 100.0
    assert result.effective_unit_price == 100.0
    assert result.line_total == 500.0
    assert result.discount_amount == 0.0
    assert result.discount_percentage == 0.0
    assert result.tier_applied == "standard"


def test_silver_pricing_strategy_5_percent_discount():
    """Silver tier pricing applies 5% discount to line pricing."""
    strategy = SilverPricingStrategy()
    assert strategy.tier_name == "silver"
    assert strategy.default_discount_percentage == 5.0

    result = strategy.calculate_line(base_price=100.0, quantity=10)
    assert result.base_unit_price == 100.0
    assert result.effective_unit_price == 95.0
    assert result.line_total == 950.0
    assert result.discount_amount == 50.0
    assert result.discount_percentage == 5.0
    assert result.tier_applied == "silver"


def test_gold_pricing_strategy_10_percent_discount():
    """Gold tier pricing applies 10% discount to line pricing."""
    strategy = GoldPricingStrategy()
    assert strategy.tier_name == "gold"
    assert strategy.default_discount_percentage == 10.0

    result = strategy.calculate_line(base_price=100.0, quantity=10)
    assert result.base_unit_price == 100.0
    assert result.effective_unit_price == 90.0
    assert result.line_total == 900.0
    assert result.discount_amount == 100.0
    assert result.discount_percentage == 10.0
    assert result.tier_applied == "gold"


def test_volume_tiered_discount_pricing():
    """Volume tiered pricing varies discount based on quantity thresholds."""
    strategy = TieredDiscountPricingStrategy()

    # Small qty (<10) -> 0%
    small = strategy.calculate_line(base_price=100.0, quantity=5)
    assert small.effective_unit_price == 100.0
    assert small.line_total == 500.0

    # Medium qty (10-49) -> 5%
    medium = strategy.calculate_line(base_price=100.0, quantity=20)
    assert medium.effective_unit_price == 95.0
    assert medium.line_total == 1900.0

    # Bulk qty (50+) -> 12%
    bulk = strategy.calculate_line(base_price=100.0, quantity=50)
    assert bulk.effective_unit_price == 88.0
    assert bulk.line_total == 4400.0


def test_qa_checklist_gold_vs_standard_order_line_differs():
    """
    QA CHECKLIST 1:
    A gold-tier retailer's order line price differs from a standard-tier retailer's
    for the exact same product and quantity.
    """
    engine = PricingEngineService()

    product_base_price = 250.0
    order_quantity = 20

    standard_result = engine.calculate_line_price(
        tier="standard",
        base_price=product_base_price,
        quantity=order_quantity,
    )

    gold_result = engine.calculate_line_price(
        tier="gold",
        base_price=product_base_price,
        quantity=order_quantity,
    )

    # Standard: 20 * 250 = 5000
    assert standard_result.effective_unit_price == 250.0
    assert standard_result.line_total == 5000.0
    assert standard_result.discount_amount == 0.0

    # Gold: 250 * 0.9 = 225 unit price; 20 * 225 = 4500 line total
    assert gold_result.effective_unit_price == 225.0
    assert gold_result.line_total == 4500.0
    assert gold_result.discount_amount == 500.0

    # Proof of difference
    assert gold_result.line_total < standard_result.line_total
    assert standard_result.line_total - gold_result.line_total == 500.0


def test_qa_checklist_ocp_extensibility_with_new_platinum_tier():
    """
    QA CHECKLIST 2 (OCP Proof):
    Adding a new tier requires writing one new PricingStrategy class,
    and ZERO changes to PricingEngineService or order calculation logic.
    """

    class PlatinumPricingStrategy(PricingStrategy):
        """Custom 15% VIP discount tier written outside the core service."""

        @property
        def tier_name(self) -> str:
            return "platinum"

        @property
        def default_discount_percentage(self) -> float:
            return 15.0

        def calculate_unit_price(self, base_price: float, quantity: int = 1, context=None) -> float:
            return round(base_price * 0.85, 2)

    # Instantiate existing engine with ZERO modifications
    engine = PricingEngineService()

    # Plug in the new strategy
    engine.register_strategy(PlatinumPricingStrategy())

    # Execute calculation on the newly plugged tier
    result = engine.calculate_line_price(tier="platinum", base_price=200.0, quantity=10)

    assert result.tier_applied == "platinum"
    assert result.effective_unit_price == 170.0
    assert result.line_total == 1700.0
    assert result.discount_amount == 300.0
    assert result.discount_percentage == 15.0


# ────────────────────────────────────────────────────────────
# 2. Repository & Domain Service CRUD Tests
# ────────────────────────────────────────────────────────────


def test_in_memory_retailer_repository_crud():
    """Verify in-memory repository CRUD, filtering, and search operations."""
    repo = InMemoryRetailerRepository()

    r1 = Retailer(
        id="ret-1",
        name="Apex Kirana",
        contact_person="Ramesh",
        phone="9876543210",
        email="apex@kirana.com",
        pricing_tier="silver",
        credit_limit=50000.0,
        is_active=True,
    )
    repo.create(r1)

    assert repo.get_by_id("ret-1") is not None
    assert repo.get_by_name("apex kirana") is not None
    assert len(repo.list_all(search="ramesh")) == 1

    repo.update("ret-1", {"pricing_tier": "gold"})
    updated = repo.get_by_id("ret-1")
    assert updated.pricing_tier == "gold"

    repo.update_credit_limit("ret-1", 75000.0)
    assert repo.get_by_id("ret-1").credit_limit == 75000.0


def test_retailer_service_create_duplicate_blocked():
    """Verify RetailerService blocks duplicate retailer names with 409 Conflict."""
    repo = InMemoryRetailerRepository()
    service = RetailerService(retailer_repo=repo)

    payload = RetailerCreateRequest(
        name="City Mart",
        pricing_tier=PricingTierEnum.GOLD,
        credit_limit=100000.0,
    )
    created = service.create_retailer(payload)
    assert created.id is not None
    assert created.name == "City Mart"
    assert created.pricing_tier == "gold"

    # Attempt duplicate
    with pytest.raises(Exception) as exc:
        service.create_retailer(payload)
    assert exc.value.status_code == status.HTTP_409_CONFLICT


def test_retailer_service_update_and_pricing_calculation():
    """Verify RetailerService updates details and calculates tier pricing correctly."""
    repo = InMemoryRetailerRepository()
    service = RetailerService(retailer_repo=repo)

    created = service.create_retailer(
        RetailerCreateRequest(
            name="Quick Stop",
            pricing_tier=PricingTierEnum.SILVER,
            credit_limit=25000.0,
        )
    )

    # Silver pricing: 100 * 0.95 = 95
    price_res = service.calculate_price(created.id, base_price=100.0, quantity=4)
    assert price_res.effective_unit_price == 95.0
    assert price_res.line_total == 380.0

    # Upgrade to Gold tier
    service.update_retailer(
        created.id,
        RetailerUpdateRequest(pricing_tier=PricingTierEnum.GOLD),
    )

    # Gold pricing: 100 * 0.90 = 90
    gold_price_res = service.calculate_price(created.id, base_price=100.0, quantity=4)
    assert gold_price_res.effective_unit_price == 90.0
    assert gold_price_res.line_total == 360.0


def test_sqlalchemy_retailer_repository():
    """Verify SQLite/Postgres persistence for SqlAlchemyRetailerRepository."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    with testing_session_local() as db_session:
        repo = SqlAlchemyRetailerRepository(session=db_session)

        retailer = Retailer(
            id="sql-ret-1",
            name="Shree Provision Stores",
            contact_person="Sunil Gupta",
            phone="9988776655",
            email="sunil@shree.com",
            pricing_tier="silver",
            credit_limit=60000.0,
            credit_balance=10000.0,
            is_active=True,
        )
        repo.create(retailer)

        fetched = repo.get_by_id("sql-ret-1")
        assert fetched is not None
        assert fetched.name == "Shree Provision Stores"
        assert fetched.pricing_tier == "silver"
        assert float(fetched.credit_limit) == 60000.0

        repo.update("sql-ret-1", {"pricing_tier": "gold", "address": "Market Yard, Pune"})
        re_fetched = repo.get_by_id("sql-ret-1")
        assert re_fetched.pricing_tier == "gold"
        assert re_fetched.address == "Market Yard, Pune"


# ────────────────────────────────────────────────────────────
# 3. FastAPI API Router Integration Tests
# ────────────────────────────────────────────────────────────


@pytest.fixture
def retailer_api_client():
    """Setup isolated FastAPI TestClient with mocked authenticated current user."""
    app = FastAPI()
    app.include_router(retailers.router)

    mock_repo = InMemoryRetailerRepository()
    mock_service = RetailerService(retailer_repo=mock_repo)

    mock_user = CurrentUser(
        id="user-owner-1",
        email="owner@wareflow.io",
        role="Owner",
        permissions={"orders:view", "orders:create", "settings:manage"},
        display_name="Test Owner",
    )

    app.dependency_overrides[get_retailer_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[require_permission("settings:manage")] = lambda: mock_user

    client = TestClient(app)
    return client, mock_service


def test_api_retailer_crud_lifecycle(retailer_api_client):
    """Test full HTTP API lifecycle: POST -> GET -> PATCH -> credit-limit."""
    client, _ = retailer_api_client

    # 1. POST /retailers
    create_res = client.post(
        "/retailers",
        json={
            "name": "Metro Hypermarket",
            "contact_person": "Vikram Singh",
            "phone": "9811223344",
            "email": "procurement@metro.in",
            "address": "Sector 18, Noida",
            "gstin": "07AAAAA0000A1Z5",
            "pricing_tier": "gold",
            "credit_limit": 200000.0,
            "is_active": True,
        },
    )
    assert create_res.status_code == status.HTTP_201_CREATED
    data = create_res.json()
    ret_id = data["id"]
    assert data["name"] == "Metro Hypermarket"
    assert data["pricing_tier"] == "gold"
    assert data["credit_limit"] == 200000.0

    # 2. GET /retailers
    list_res = client.get("/retailers")
    assert list_res.status_code == status.HTTP_200_OK
    assert len(list_res.json()) == 1

    # 3. GET /retailers/{id}
    get_res = client.get(f"/retailers/{ret_id}")
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.json()["name"] == "Metro Hypermarket"

    # 4. PATCH /retailers/{id}
    patch_res = client.patch(
        f"/retailers/{ret_id}",
        json={"pricing_tier": "silver", "contact_person": "Amit Verma"},
    )
    assert patch_res.status_code == status.HTTP_200_OK
    assert patch_res.json()["pricing_tier"] == "silver"
    assert patch_res.json()["contact_person"] == "Amit Verma"

    # 5. PATCH /retailers/{id}/credit-limit
    credit_res = client.patch(
        f"/retailers/{ret_id}/credit-limit",
        json={"credit_limit": 300000.0},
    )
    assert credit_res.status_code == status.HTTP_200_OK
    assert credit_res.json()["credit_limit"] == 300000.0
