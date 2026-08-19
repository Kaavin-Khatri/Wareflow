"""
Unit and integration tests for Step 11.2 — Tier-Priced Searchable Retailer Product Catalog.

Validates:
1. Tier-based price resolution (Gold / Silver / Standard) for identical catalog items.
2. Privacy-preserving stock availability bands ('Available' / 'Low' / 'Out') with zero exact inventory leakage.
3. Client/Server search and category filtering behavior.
4. HTTP route security and retailer tenant boundary enforcement.
"""

from fastapi import FastAPI, status
from fastapi.testclient import TestClient
import pytest

from app.api.routers import portal
from app.core.di import get_portal_auth_service
from app.core.security import CurrentUser, get_current_user, require_portal_retailer
from app.models.catalog import Category, Product
from app.models.portal import RetailerUser
from app.models.profile import Profile
from app.models.retailer import Retailer
from app.models.warehouse import StockBatch, Warehouse
from app.repositories.impl.product_repository import InMemoryProductRepository
from app.repositories.impl.profile_repository import InMemoryProfileRepository
from app.repositories.impl.retailer_repository import InMemoryRetailerRepository
from app.repositories.impl.retailer_user_repository import InMemoryRetailerUserRepository
from app.repositories.impl.stock_repository import InMemoryStockRepository
from app.services.pricing_strategy import PricingEngineService
from app.services.portal_auth_service import PortalAuthService


def _setup_portal_catalog_env():
    # 1. Retailers with different tiers
    ret_standard = Retailer(
        id="ret-standard-1",
        name="Standard Grocery Store",
        email="standard@store.com",
        pricing_tier="standard",
        credit_limit=100000.0,
        credit_balance=0.0,
        is_active=True,
    )
    ret_silver = Retailer(
        id="ret-silver-1",
        name="Silver Hypermarket",
        email="silver@hyper.com",
        pricing_tier="silver",
        credit_limit=500000.0,
        credit_balance=0.0,
        is_active=True,
    )
    ret_gold = Retailer(
        id="ret-gold-1",
        name="Gold Wholesale Enterprise",
        email="gold@enterprise.com",
        pricing_tier="gold",
        credit_limit=1000000.0,
        credit_balance=0.0,
        is_active=True,
    )
    retailer_repo = InMemoryRetailerRepository(initial_data=[ret_standard, ret_silver, ret_gold])

    # 2. Retailer Users
    user_std = RetailerUser(id="uid_ret_std", retailer_id="ret-standard-1", email="standard@store.com", is_active=True)
    user_sil = RetailerUser(id="uid_ret_sil", retailer_id="ret-silver-1", email="silver@hyper.com", is_active=True)
    user_gld = RetailerUser(id="uid_ret_gld", retailer_id="ret-gold-1", email="gold@enterprise.com", is_active=True)
    retailer_user_repo = InMemoryRetailerUserRepository(initial_users=[user_std, user_sil, user_gld])

    # 3. Staff Profile
    staff_profile = Profile(id="uid_staff_admin", email="admin@wareflow.com", is_active=True, role_id="role-admin")
    profile_repo = InMemoryProfileRepository(initial_profiles=[staff_profile])

    # 4. Categories & Products
    cat_grains = Category(id="cat-grains", name="Grains & Cereals")
    cat_beverages = Category(id="cat-beverages", name="Beverages")

    # Product A: In Stock (Base wholesale price: ₹1000.00, reorder_point: 20)
    prod_rice = Product(
        id="prod-rice-1",
        sku="RIC-BAS-001",
        name="Premium Basmati Rice 25kg",
        description="Aged royal basmati rice bag",
        content_details="25kg Bag, Grade A",
        wholesale_price=1000.00,
        cost_price=750.00,
        category_id="cat-grains",
        reorder_point=20,
        reorder_qty=50,
        unit="Bag",
        hsn_code="1006.30",
        is_active=True,
    )
    # Product B: Low Stock (Base wholesale price: ₹500.00, reorder_point: 30, on_hand: 15)
    prod_tea = Product(
        id="prod-tea-1",
        sku="TEA-ASS-001",
        name="Assam CTC Premium Tea 5kg",
        description="Strong orthodox black tea",
        content_details="5kg Box",
        wholesale_price=500.00,
        cost_price=350.00,
        category_id="cat-beverages",
        reorder_point=30,
        reorder_qty=40,
        unit="Box",
        hsn_code="0902.30",
        is_active=True,
    )
    # Product C: Out of Stock (Base wholesale price: ₹200.00, on_hand: 0)
    prod_sugar = Product(
        id="prod-sugar-1",
        sku="SUG-REF-001",
        name="Refined White Sugar 50kg",
        description="Pure cane sugar",
        content_details="50kg Bag",
        wholesale_price=200.00,
        cost_price=150.00,
        category_id="cat-grains",
        reorder_point=10,
        reorder_qty=20,
        unit="Bag",
        hsn_code="1701.99",
        is_active=True,
    )

    product_repo = InMemoryProductRepository(
        seed_products=[prod_rice, prod_tea, prod_sugar],
        seed_categories=[cat_grains, cat_beverages],
    )

    # 5. Stock Batches
    warehouse = Warehouse(id="wh-main", name="Central Warehouse", location="Mumbai", is_active=True)
    batch_rice = StockBatch(id="b-rice-1", product_id="prod-rice-1", warehouse_id="wh-main", batch_no="B-R1", quantity=100.0)
    batch_tea = StockBatch(id="b-tea-1", product_id="prod-tea-1", warehouse_id="wh-main", batch_no="B-T1", quantity=15.0)
    # sugar has 0 stock batches

    stock_repo = InMemoryStockRepository(
        warehouses=[warehouse],
        products=[prod_rice, prod_tea, prod_sugar],
        batches=[batch_rice, batch_tea],
    )

    pricing_engine = PricingEngineService()
    portal_service = PortalAuthService(
        retailer_user_repo=retailer_user_repo,
        retailer_repo=retailer_repo,
        profile_repo=profile_repo,
        product_repo=product_repo,
        stock_repo=stock_repo,
        pricing_engine=pricing_engine,
    )

    return {
        "service": portal_service,
        "product_repo": product_repo,
        "stock_repo": stock_repo,
        "pricing_engine": pricing_engine,
        "ret_standard": ret_standard,
        "ret_silver": ret_silver,
        "ret_gold": ret_gold,
    }


def test_retailers_on_different_tiers_see_different_prices():
    """QA 1: Two retailers on different pricing tiers see different prices for identical product."""
    env = _setup_portal_catalog_env()
    service: PortalAuthService = env["service"]

    user_std = CurrentUser(id="uid_ret_std", email="standard@store.com", role="Retailer", permissions=set(), account_type="retailer", retailer_id="ret-standard-1")
    user_sil = CurrentUser(id="uid_ret_sil", email="silver@hyper.com", role="Retailer", permissions=set(), account_type="retailer", retailer_id="ret-silver-1")
    user_gld = CurrentUser(id="uid_ret_gld", email="gold@enterprise.com", role="Retailer", permissions=set(), account_type="retailer", retailer_id="ret-gold-1")

    catalog_std = service.get_retailer_catalog(user_std)
    catalog_sil = service.get_retailer_catalog(user_sil)
    catalog_gld = service.get_retailer_catalog(user_gld)

    # Find Rice (Base ₹1000.00)
    rice_std = next(p for p in catalog_std if p.sku == "RIC-BAS-001")
    rice_sil = next(p for p in catalog_sil if p.sku == "RIC-BAS-001")
    rice_gld = next(p for p in catalog_gld if p.sku == "RIC-BAS-001")

    # Standard (0% discount)
    assert rice_std.base_price == 1000.00
    assert rice_std.effective_price == 1000.00
    assert rice_std.discount_percentage == 0.0
    assert rice_std.pricing_tier == "standard"

    # Silver (5% discount) -> ₹950.00
    assert rice_sil.base_price == 1000.00
    assert rice_sil.effective_price == 950.00
    assert rice_sil.discount_percentage == 5.0
    assert rice_sil.pricing_tier == "silver"

    # Gold (10% discount) -> ₹900.00
    assert rice_gld.base_price == 1000.00
    assert rice_gld.effective_price == 900.00
    assert rice_gld.discount_percentage == 10.0
    assert rice_gld.pricing_tier == "gold"

    # Strict check: prices differ across tiers for identical catalog item
    assert rice_gld.effective_price < rice_sil.effective_price < rice_std.effective_price


def test_stock_availability_bands_and_privacy_guarantee():
    """QA 2: Stock status displays privacy-preserving Available / Low / Out with zero exact quantity leak."""
    env = _setup_portal_catalog_env()
    service: PortalAuthService = env["service"]
    user_std = CurrentUser(id="uid_ret_std", email="standard@store.com", role="Retailer", permissions=set(), account_type="retailer", retailer_id="ret-standard-1")

    catalog = service.get_retailer_catalog(user_std)

    rice = next(p for p in catalog if p.sku == "RIC-BAS-001")  # on_hand = 100 > reorder_point 20
    tea = next(p for p in catalog if p.sku == "TEA-ASS-001")    # on_hand = 15 <= reorder_point 30
    sugar = next(p for p in catalog if p.sku == "SUG-REF-001")  # on_hand = 0

    assert rice.availability == "Available"
    assert tea.availability == "Low"
    assert sugar.availability == "Out"

    # Privacy guarantee: dump model and verify no 'on_hand', 'quantity', 'stock_batches', etc. exist
    item_dict = rice.model_dump()
    assert "total_on_hand" not in item_dict
    assert "quantity" not in item_dict
    assert "on_hand" not in item_dict
    assert "warehouses" not in item_dict


def test_catalog_search_and_category_filtering():
    """QA 3: Search and category filters narrow catalog results correctly."""
    env = _setup_portal_catalog_env()
    service: PortalAuthService = env["service"]
    user_std = CurrentUser(id="uid_ret_std", email="standard@store.com", role="Retailer", permissions=set(), account_type="retailer", retailer_id="ret-standard-1")

    # 1. Search by name "Basmati"
    results_search = service.get_retailer_catalog(user_std, search="Basmati")
    assert len(results_search) == 1
    assert results_search[0].sku == "RIC-BAS-001"

    # 2. Search by SKU "TEA"
    results_sku = service.get_retailer_catalog(user_std, search="TEA")
    assert len(results_sku) == 1
    assert results_sku[0].sku == "TEA-ASS-001"

    # 3. Filter by category "cat-beverages"
    results_cat_bev = service.get_retailer_catalog(user_std, category_id="cat-beverages")
    assert len(results_cat_bev) == 1
    assert results_cat_bev[0].sku == "TEA-ASS-001"

    # 4. Filter by category "cat-grains"
    results_cat_grains = service.get_retailer_catalog(user_std, category_id="cat-grains")
    assert len(results_cat_grains) == 2
    skus = {p.sku for p in results_cat_grains}
    assert "RIC-BAS-001" in skus
    assert "SUG-REF-001" in skus


def test_portal_catalog_http_endpoints_and_cross_boundary_guards():
    """Test HTTP GET /portal/catalog and GET /portal/categories endpoints and RBAC guards."""
    env = _setup_portal_catalog_env()
    service = env["service"]

    app = FastAPI()
    app.include_router(portal.router)
    app.dependency_overrides[get_portal_auth_service] = lambda: service

    current_retailer_user = CurrentUser(
        id="uid_ret_sil",
        email="silver@hyper.com",
        role="Retailer",
        permissions=set(),
        account_type="retailer",
        retailer_id="ret-silver-1",
    )
    app.dependency_overrides[require_portal_retailer] = lambda: current_retailer_user
    app.dependency_overrides[get_current_user] = lambda: current_retailer_user

    client = TestClient(app)

    # 1. GET /portal/catalog as Silver Retailer
    res = client.get("/portal/catalog")
    assert res.status_code == status.HTTP_200_OK
    items = res.json()
    assert len(items) == 3
    rice_item = next(i for i in items if i["sku"] == "RIC-BAS-001")
    assert rice_item["effective_price"] == 950.00
    assert rice_item["pricing_tier"] == "silver"
    assert rice_item["availability"] == "Available"

    # 2. GET /portal/categories
    cat_res = client.get("/portal/categories")
    assert cat_res.status_code == status.HTTP_200_OK
    cats = cat_res.json()
    assert len(cats) >= 2
    cat_names = {c["name"] for c in cats}
    assert "Grains & Cereals" in cat_names
    assert "Beverages" in cat_names

    # 3. Staff account rejected from GET /portal/catalog with 403
    staff_user = CurrentUser(
        id="uid_staff_admin",
        email="admin@wareflow.com",
        role="Admin",
        account_type="staff",
        retailer_id=None,
        permissions={"inventory:view"},
    )
    # Remove override to let real require_portal_retailer execute
    del app.dependency_overrides[require_portal_retailer]
    app.dependency_overrides[get_current_user] = lambda: staff_user

    forbidden_res = client.get("/portal/catalog")
    assert forbidden_res.status_code == status.HTTP_403_FORBIDDEN
    assert "Retailer portal access only" in forbidden_res.json()["detail"]
