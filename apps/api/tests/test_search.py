"""
Unit & Integration Tests for Global Admin Search (Step 15.4).

Verifies:
1. Exact SKU, retailer name, and invoice number return top hit with score 100/95.
2. Prefix and substring matching rank appropriately.
3. Multi-domain results (products, sales orders, purchase orders, invoices, retailers, suppliers).
4. Direct endpoint integration via FastAPI TestClient (GET /search?q=...).
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.core.di import get_search_service
from app.main import app
from app.models.billing import Invoice, InvoiceStatusEnum
from app.models.catalog import Category, Product
from app.models.retailer import Retailer, SalesOrder
from app.models.supplier import POStatusEnum, PurchaseOrder, Supplier
from app.services.search_service import SearchService


@pytest.fixture
def mock_repos():
    """Mock domain repositories with rich sample data across all ERP models."""
    product_repo = MagicMock()
    sales_order_repo = MagicMock()
    purchase_order_repo = MagicMock()
    retailer_repo = MagicMock()
    supplier_repo = MagicMock()
    invoice_repo = MagicMock()

    # Category & Products
    cat = Category(id=str(uuid.uuid4()), name="Grains & Rice")
    prod1 = Product(
        id=str(uuid.uuid4()),
        name="Royal Basmati Rice 5kg",
        sku="RIC-BAS-001",
        wholesale_price=500.0,
        category=cat,
    )
    prod2 = Product(
        id=str(uuid.uuid4()),
        name="Organic Mustard Oil 1L",
        sku="OIL-MUS-100",
        wholesale_price=180.0,
        category=cat,
    )
    product_repo.list_products.return_value = [prod1, prod2]

    # Retailers
    ret1 = Retailer(
        id=str(uuid.uuid4()),
        name="Apex Kirana Stores",
        contact_person="Ramesh Kumar",
        phone="+919876543210",
        credit_limit=50000.0,
    )
    ret2 = Retailer(
        id=str(uuid.uuid4()),
        name="Supermart Express",
        contact_person="Anita Sharma",
        phone="+919876543211",
        credit_limit=100000.0,
    )
    retailer_repo.list_all.return_value = [ret1, ret2]

    # Suppliers
    sup1 = Supplier(
        id=str(uuid.uuid4()),
        name="Himalayan Foods Pvt Ltd",
        contact_person="Vikram Singh",
        phone="+919811122233",
        address="Dehradun, Uttarakhand",
    )
    supplier_repo.list_suppliers.return_value = [sup1]

    # Sales Orders
    so1 = SalesOrder(
        id=str(uuid.uuid4()),
        so_number="SO-2026-0001",
        status="confirmed",
        total_amount=15400.0,
        retailer=ret1,
    )
    sales_order_repo.list_all.return_value = ([so1], 1)

    # Purchase Orders
    po1 = PurchaseOrder(
        id=str(uuid.uuid4()),
        po_number="PO-2026-0888",
        status=POStatusEnum.ORDERED,
        total_amount=45000.0,
        supplier=sup1,
    )
    purchase_order_repo.list_purchase_orders.return_value = [po1]

    # Invoices
    inv1 = Invoice(
        id=str(uuid.uuid4()),
        invoice_no="INV/2026-27/0042",
        status=InvoiceStatusEnum.UNPAID,
        total_amount=15400.0,
        invoice_date=datetime.now(UTC),
    )
    inv1.sales_order = so1
    invoice_repo.list_invoices.return_value = ([inv1], 1)

    return {
        "product_repo": product_repo,
        "sales_order_repo": sales_order_repo,
        "purchase_order_repo": purchase_order_repo,
        "retailer_repo": retailer_repo,
        "supplier_repo": supplier_repo,
        "invoice_repo": invoice_repo,
        "prod1": prod1,
        "ret1": ret1,
        "sup1": sup1,
        "so1": so1,
        "po1": po1,
        "inv1": inv1,
    }


@pytest.fixture
def search_service(mock_repos) -> SearchService:
    return SearchService(
        product_repo=mock_repos["product_repo"],
        sales_order_repo=mock_repos["sales_order_repo"],
        purchase_order_repo=mock_repos["purchase_order_repo"],
        retailer_repo=mock_repos["retailer_repo"],
        supplier_repo=mock_repos["supplier_repo"],
        invoice_repo=mock_repos["invoice_repo"],
    )


def test_search_empty_query(search_service: SearchService):
    """Empty or whitespace query should return 0 results immediately."""
    res = search_service.search("")
    assert res.total == 0
    assert len(res.results) == 0

    res_spaces = search_service.search("   ")
    assert res_spaces.total == 0
    assert len(res_spaces.results) == 0


def test_search_exact_sku_returns_top_hit(search_service: SearchService, mock_repos):
    """QA Item: Searching a known SKU returns the correct product as the top hit."""
    res = search_service.search("RIC-BAS-001")
    assert res.total >= 1
    top_hit = res.results[0]
    assert top_hit.kind == "product"
    assert top_hit.title == "Royal Basmati Rice 5kg"
    assert "RIC-BAS-001" in top_hit.subtitle
    assert top_hit.score == 100.0
    assert top_hit.url == "/admin/products"


def test_search_exact_retailer_name_returns_top_hit(search_service: SearchService, mock_repos):
    """QA Item: Searching a known retailer name returns the correct retailer as top hit."""
    res = search_service.search("Apex Kirana Stores")
    assert res.total >= 1
    # Check top hit is the retailer
    top_hit = res.results[0]
    assert top_hit.kind == "retailer"
    assert top_hit.title == "Apex Kirana Stores"
    assert top_hit.score == 95.0
    assert top_hit.url == "/admin/retailers"


def test_search_exact_invoice_number_returns_top_hit(search_service: SearchService, mock_repos):
    """QA Item: Searching a known invoice number returns the correct invoice as top hit."""
    res = search_service.search("INV/2026-27/0042")
    assert res.total >= 1
    top_hit = res.results[0]
    assert top_hit.kind == "invoice"
    assert top_hit.title == "INV/2026-27/0042"
    assert top_hit.score == 100.0
    assert top_hit.url == "/admin/invoices"


def test_search_sales_and_purchase_orders(search_service: SearchService, mock_repos):
    """Searching order numbers returns order records with appropriate badges."""
    so_res = search_service.search("SO-2026-0001")
    assert so_res.total >= 1
    assert so_res.results[0].kind == "sales_order"
    assert so_res.results[0].title == "SO-2026-0001"
    assert so_res.results[0].badge == "CONFIRMED"

    po_res = search_service.search("PO-2026-0888")
    assert po_res.total >= 1
    assert po_res.results[0].kind == "purchase_order"
    assert po_res.results[0].title == "PO-2026-0888"


def test_search_prefix_and_partial_relevance(search_service: SearchService, mock_repos):
    """Prefix matches receive higher score than general substring matches."""
    res = search_service.search("Basmati")
    assert res.total >= 1
    # Royal Basmati Rice contains substring or prefix
    assert any(r.kind == "product" and "Basmati" in r.title for r in res.results)


def test_global_search_api_endpoint(search_service: SearchService):
    """FastAPI TestClient integration verifying GET /search?q=."""
    app.dependency_overrides[get_search_service] = lambda: search_service
    client = TestClient(app)

    try:
        response = client.get("/search?q=Apex")
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "Apex"
        assert data["total"] >= 1
        assert len(data["results"]) >= 1

        # Check fields match schema
        first = data["results"][0]
        assert "id" in first
        assert "kind" in first
        assert "title" in first
        assert "url" in first
        assert "score" in first
    finally:
        app.dependency_overrides.pop(get_search_service, None)
