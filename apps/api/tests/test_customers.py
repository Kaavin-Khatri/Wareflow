"""Comprehensive unit and integration tests for Direct Customer management and shared sales order pipeline."""

from datetime import UTC, datetime

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.di import (
    get_customer_repository,
    get_customer_service,
    get_pricing_engine_service,
    get_product_repository,
    get_retailer_repository,
    get_sales_order_repository,
    get_sales_order_service,
    get_stock_repository,
)
from app.core.security import CurrentUser, get_current_user
from app.main import app
from app.models.retailer import BuyerTypeEnum, SOStatusEnum
from app.repositories.impl.customer_repository import InMemoryCustomerRepository
from app.repositories.impl.product_repository import InMemoryProductRepository
from app.repositories.impl.retailer_repository import InMemoryRetailerRepository
from app.repositories.impl.sales_order_repository import InMemorySalesOrderRepository
from app.repositories.impl.stock_repository import InMemoryStockRepository
from app.schemas.customers import CustomerCreateRequest, CustomerUpdateRequest
from app.schemas.sales_orders import (
    SalesOrderCreateRequest,
    SalesOrderItemCreateRequest,
    SalesOrderStatusUpdateRequest,
)
from app.services.customer_service import CustomerService
from app.services.pricing_strategy import PricingEngineService
from app.services.sales_order_service import SalesOrderService


@pytest.fixture
def clean_repos():
    cust_repo = InMemoryCustomerRepository()
    so_repo = InMemorySalesOrderRepository()
    stock_repo = InMemoryStockRepository()
    prod_repo = InMemoryProductRepository()
    ret_repo = InMemoryRetailerRepository()
    pricing_engine = PricingEngineService()

    cust_service = CustomerService(customer_repo=cust_repo, so_repo=so_repo)
    so_service = SalesOrderService(
        so_repo=so_repo,
        retailer_repo=ret_repo,
        stock_repo=stock_repo,
        product_repo=prod_repo,
        pricing_engine=pricing_engine,
        customer_repo=cust_repo,
    )

    return {
        "cust_repo": cust_repo,
        "so_repo": so_repo,
        "stock_repo": stock_repo,
        "prod_repo": prod_repo,
        "ret_repo": ret_repo,
        "pricing_engine": pricing_engine,
        "cust_service": cust_service,
        "so_service": so_service,
    }


def test_customer_crud_lifecycle(clean_repos):
    cust_service = clean_repos["cust_service"]

    # 1. Create customer
    req = CustomerCreateRequest(
        name="Ramesh Gupta",
        phone="+919876543210",
        email="ramesh.gupta@example.com",
        address="Shop 4, Chandni Chowk, Delhi",
        notes="Walk-in bulk buyer for pulses",
    )
    created = cust_service.create_customer(req)
    assert created.id is not None
    assert created.name == "Ramesh Gupta"
    assert created.total_orders_count == 0
    assert created.total_spend == 0.0

    # 2. Get customer by ID
    fetched = cust_service.get_customer(created.id)
    assert fetched.id == created.id
    assert fetched.email == "ramesh.gupta@example.com"

    # 3. List with search
    list_res = cust_service.list_customers(search="ramesh")
    assert list_res.total == 1
    assert list_res.items[0].id == created.id

    # 4. Update customer
    update_req = CustomerUpdateRequest(phone="+919876543999", notes="Preferred payment: UPI")
    updated = cust_service.update_customer(created.id, update_req)
    assert updated.phone == "+919876543999"
    assert updated.notes == "Preferred payment: UPI"

    # 5. Delete customer
    cust_service.delete_customer(created.id)
    with pytest.raises(HTTPException) as exc:
        cust_service.get_customer(created.id)
    assert exc.value.status_code == 404


def test_customer_sales_order_skips_credit_check_and_deducts_fifo_stock(clean_repos):
    cust_service = clean_repos["cust_service"]
    so_service = clean_repos["so_service"]
    prod_repo = clean_repos["prod_repo"]
    stock_repo = clean_repos["stock_repo"]

    # Seed product and inventory batches
    prod_repo.create_product(
        {
            "id": "prod-rice-001",
            "sku": "RIC-BAS-001",
            "name": "Premium Basmati Rice 10kg",
            "cost_price": 400.0,
            "wholesale_price": 600.0,
        }
    )

    stock_repo.batches["batch-001"] = {
        "id": "batch-001",
        "product_id": "prod-rice-001",
        "warehouse_id": "wh-delhi",
        "batch_no": "B-001",
        "quantity": 15.0,
        "expiry_date": datetime(2027, 1, 1, tzinfo=UTC),
    }

    # Register walk-in customer
    cust = cust_service.create_customer(
        CustomerCreateRequest(name="Sunita Sharma", phone="+919811223344")
    )

    # Create Sales Order for Customer (buyer_type=customer)
    order_req = SalesOrderCreateRequest(
        buyer_type=BuyerTypeEnum.CUSTOMER,
        customer_id=cust.id,
        items=[
            SalesOrderItemCreateRequest(
                product_id="prod-rice-001",
                qty=10.0,
            )
        ],
    )

    order = so_service.create_order(order_req)
    assert order.buyer_type == BuyerTypeEnum.CUSTOMER
    assert order.customer_id == cust.id
    assert order.customer_name == "Sunita Sharma"
    assert order.total_amount == 6000.0  # 10 * 600
    assert order.status == SOStatusEnum.DRAFT

    # Confirm Order: MUST skip credit verification (cash customer) and deduct FIFO batch
    confirmed = so_service.confirm_order(order.id)
    assert confirmed.status == SOStatusEnum.CONFIRMED

    # Verify inventory was deducted
    assert stock_repo.batches["batch-001"]["quantity"] == 5.0  # 15 - 10

    # Verify stock movement ledger entry
    movements = stock_repo.movements
    assert len(movements) == 1
    assert movements[0]["type"] == "out"
    assert movements[0]["quantity"] == 10.0
    assert movements[0]["reference_type"] == "sales_order"


def test_customer_sales_order_cancellation_restores_stock(clean_repos):
    cust_service = clean_repos["cust_service"]
    so_service = clean_repos["so_service"]
    prod_repo = clean_repos["prod_repo"]
    stock_repo = clean_repos["stock_repo"]

    prod_repo.create_product(
        {
            "id": "prod-oil-001",
            "sku": "OIL-MUS-005",
            "name": "Mustard Oil 5L",
            "cost_price": 500.0,
            "wholesale_price": 700.0,
        }
    )

    stock_repo.batches["batch-oil-001"] = {
        "id": "batch-oil-001",
        "product_id": "prod-oil-001",
        "warehouse_id": "wh-delhi",
        "batch_no": "B-OIL-01",
        "quantity": 20.0,
        "expiry_date": datetime(2027, 6, 1, tzinfo=UTC),
    }

    cust = cust_service.create_customer(CustomerCreateRequest(name="Anil Verma"))

    order = so_service.create_order(
        SalesOrderCreateRequest(
            buyer_type=BuyerTypeEnum.CUSTOMER,
            customer_id=cust.id,
            items=[SalesOrderItemCreateRequest(product_id="prod-oil-001", qty=5.0)],
        )
    )

    so_service.confirm_order(order.id)
    assert stock_repo.batches["batch-oil-001"]["quantity"] == 15.0

    # Cancel confirmed customer order -> restores stock cleanly without credit check error
    cancelled = so_service.update_status(
        order.id, SalesOrderStatusUpdateRequest(status=SOStatusEnum.CANCELLED)
    )
    assert cancelled.status == SOStatusEnum.CANCELLED
    assert stock_repo.batches["batch-oil-001"]["quantity"] == 20.0



def test_create_order_invalid_customer_rejected(clean_repos):
    so_service = clean_repos["so_service"]
    prod_repo = clean_repos["prod_repo"]

    prod_repo.create_product(
        {
            "id": "prod-p1",
            "sku": "P-001",
            "name": "Test Item",
            "cost_price": 10.0,
            "wholesale_price": 20.0,
        }
    )

    req = SalesOrderCreateRequest(
        buyer_type=BuyerTypeEnum.CUSTOMER,
        customer_id="nonexistent-customer-id",
        items=[SalesOrderItemCreateRequest(product_id="prod-p1", qty=1.0)],
    )

    with pytest.raises(HTTPException) as exc:
        so_service.create_order(req)
    assert exc.value.status_code == 404
    assert "Customer 'nonexistent-customer-id' not found" in str(exc.value.detail)


def test_cannot_delete_customer_with_existing_orders(clean_repos):
    cust_service = clean_repos["cust_service"]
    so_service = clean_repos["so_service"]
    prod_repo = clean_repos["prod_repo"]

    prod_repo.create_product(
        {
            "id": "prod-p2",
            "sku": "P-002",
            "name": "Test Item 2",
            "cost_price": 10.0,
            "wholesale_price": 20.0,
        }
    )

    cust = cust_service.create_customer(CustomerCreateRequest(name="Deepak Joshi"))

    so_service.create_order(
        SalesOrderCreateRequest(
            buyer_type=BuyerTypeEnum.CUSTOMER,
            customer_id=cust.id,
            items=[SalesOrderItemCreateRequest(product_id="prod-p2", qty=2.0)],
        )
    )

    # Attempt delete customer with order -> 422
    with pytest.raises(HTTPException) as exc:
        cust_service.delete_customer(cust.id)
    assert exc.value.status_code == 422
    assert "Cannot delete customer 'Deepak Joshi' with existing sales orders" in str(
        exc.value.detail
    )


def test_customer_api_endpoints():
    cust_repo = InMemoryCustomerRepository()
    so_repo = InMemorySalesOrderRepository()
    prod_repo = InMemoryProductRepository()
    stock_repo = InMemoryStockRepository()
    ret_repo = InMemoryRetailerRepository()
    pricing_engine = PricingEngineService()

    cust_service = CustomerService(customer_repo=cust_repo, so_repo=so_repo)
    so_service = SalesOrderService(
        so_repo=so_repo,
        retailer_repo=ret_repo,
        stock_repo=stock_repo,
        product_repo=prod_repo,
        pricing_engine=pricing_engine,
        customer_repo=cust_repo,
    )

    fake_user = CurrentUser(
        id="user-admin-1",
        email="admin@wareflow.internal",
        role="Admin",
        permissions=["inventory:manage", "orders:create", "orders:view"],
    )

    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[get_customer_repository] = lambda: cust_repo
    app.dependency_overrides[get_customer_service] = lambda: cust_service
    app.dependency_overrides[get_sales_order_repository] = lambda: so_repo
    app.dependency_overrides[get_sales_order_service] = lambda: so_service
    app.dependency_overrides[get_product_repository] = lambda: prod_repo
    app.dependency_overrides[get_stock_repository] = lambda: stock_repo
    app.dependency_overrides[get_retailer_repository] = lambda: ret_repo
    app.dependency_overrides[get_pricing_engine_service] = lambda: pricing_engine

    client = TestClient(app)

    # 1. POST /customers
    create_res = client.post(
        "/customers",
        json={
            "name": "Kavita Singh",
            "phone": "+919123456789",
            "email": "kavita@example.com",
            "address": "Sector 18, Noida",
            "notes": "Walk-in retail buyer",
        },
    )
    assert create_res.status_code == 201
    cust_data = create_res.json()
    cust_id = cust_data["id"]
    assert cust_data["name"] == "Kavita Singh"

    # 2. GET /customers
    list_res = client.get("/customers?search=Kavita")
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1
    assert list_res.json()[0]["id"] == cust_id

    # 3. GET /customers/{id}
    get_res = client.get(f"/customers/{cust_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Kavita Singh"

    # 4. PATCH /customers/{id}
    patch_res = client.patch(
        f"/customers/{cust_id}",
        json={"notes": "Prefers evening delivery"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["notes"] == "Prefers evening delivery"

    # Cleanup overrides
    app.dependency_overrides.clear()
