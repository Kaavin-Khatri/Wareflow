"""
Unit & Integration Tests for Step 16.2 Analytics:
- Supplier Performance (On-time rate, fulfillment accuracy, return rate)
- Retailer Performance (Revenue ranking, frequency trend, churn-risk heuristic)
- Warehouse Breakdown (Valuation, 30d inbound/outbound throughput)
- Shrinkage (Damage & loss adjustments, dimension rollups)
"""

from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_current_user
from app.main import app
from app.models.catalog import Product
from app.models.inventory import StockMovement, StockMovementTypeEnum
from app.models.profile import Profile
from app.models.retailer import Retailer, SalesOrder, SOStatusEnum
from app.models.returns import PurchaseReturn, PurchaseReturnItem, PurchaseReturnStatusEnum
from app.models.supplier import POStatusEnum, PurchaseOrder, PurchaseOrderItem, Supplier
from app.models.warehouse import StockBatch, Warehouse
from app.repositories.impl.product_repository import InMemoryProductRepository
from app.repositories.impl.purchase_order_repository import InMemoryPurchaseOrderRepository
from app.repositories.impl.retailer_repository import InMemoryRetailerRepository
from app.repositories.impl.sales_order_repository import InMemorySalesOrderRepository
from app.repositories.impl.stock_repository import InMemoryStockRepository
from app.repositories.impl.supplier_repository import InMemorySupplierRepository
from app.services.retailer_performance_service import RetailerPerformanceService
from app.services.shrinkage_service import ShrinkageService
from app.services.supplier_performance_service import SupplierPerformanceService
from app.services.warehouse_analytics_service import WarehouseAnalyticsService


class InMemoryPurchaseReturnRepository:
    """In-memory stub for PurchaseReturnRepositoryInterface."""

    def __init__(self, returns: list[PurchaseReturn] | None = None) -> None:
        self._returns: list[PurchaseReturn] = returns or []

    def create(self, purchase_order_id: str, supplier_id: str, reason: str | None, items: list[dict]) -> PurchaseReturn:
        ret = PurchaseReturn(
            id=f"ret-{len(self._returns)+1}",
            purchase_order_id=purchase_order_id,
            supplier_id=supplier_id,
            status=PurchaseReturnStatusEnum.REQUESTED,
            reason=reason,
            items=[PurchaseReturnItem(id=f"ri-{i}", return_id=f"ret-{len(self._returns)+1}", product_id=it["product_id"], qty=it["qty"]) for i, it in enumerate(items)],
        )
        self._returns.append(ret)
        return ret

    def get_by_id(self, return_id: str) -> PurchaseReturn | None:
        return next((r for r in self._returns if r.id == return_id), None)

    def list_all(self, supplier_id: str | None = None, status: PurchaseReturnStatusEnum | None = None, purchase_order_id: str | None = None) -> list[PurchaseReturn]:
        res = self._returns
        if supplier_id:
            res = [r for r in res if r.supplier_id == supplier_id]
        if status:
            res = [r for r in res if r.status == status]
        if purchase_order_id:
            res = [r for r in res if r.purchase_order_id == purchase_order_id]
        return res

    def update_status(self, return_id: str, status: PurchaseReturnStatusEnum, credit_note_ref: str | None = None) -> PurchaseReturn | None:
        ret = self.get_by_id(return_id)
        if ret:
            ret.status = status
            ret.credit_note_ref = credit_note_ref
        return ret


def test_supplier_performance_hand_computed_check():
    """QA Item 1: On-time delivery rate matches a hand-computed check against 3 crafted POs with known expected/actual dates."""
    now = datetime(2026, 8, 24, 12, 0, 0, tzinfo=timezone.utc)
    sup = Supplier(id="sup-1", name="Apex FMCG Ltd", is_active=True)
    sup_repo = InMemorySupplierRepository([sup])

    # 3 Crafted POs:
    # PO 1: Expected 2026-08-10, Received order_date 2026-08-08 -> ON TIME
    # PO 2: Expected 2026-08-15, Received order_date 2026-08-15 -> ON TIME (on same day)
    # PO 3: Expected 2026-08-18, Received order_date 2026-08-20 -> LATE
    po1 = PurchaseOrder(
        id="po-1",
        po_number="PO-001",
        supplier_id="sup-1",
        status=POStatusEnum.RECEIVED,
        order_date=datetime(2026, 8, 8, 10, 0, 0, tzinfo=timezone.utc),
        created_at=datetime(2026, 8, 8, 10, 0, 0, tzinfo=timezone.utc),
        expected_date=date(2026, 8, 10),
        total_amount=10000.0,
        items=[PurchaseOrderItem(id="poi-1", po_id="po-1", product_id="p-1", qty_ordered=100.0, qty_received=100.0, unit_cost=100.0)],
    )
    po2 = PurchaseOrder(
        id="po-2",
        po_number="PO-002",
        supplier_id="sup-1",
        status=POStatusEnum.RECEIVED,
        order_date=datetime(2026, 8, 15, 14, 0, 0, tzinfo=timezone.utc),
        created_at=datetime(2026, 8, 15, 14, 0, 0, tzinfo=timezone.utc),
        expected_date=date(2026, 8, 15),
        total_amount=15000.0,
        items=[PurchaseOrderItem(id="poi-2", po_id="po-2", product_id="p-1", qty_ordered=150.0, qty_received=150.0, unit_cost=100.0)],
    )
    po3 = PurchaseOrder(
        id="po-3",
        po_number="PO-003",
        supplier_id="sup-1",
        status=POStatusEnum.RECEIVED,
        order_date=datetime(2026, 8, 20, 11, 0, 0, tzinfo=timezone.utc),
        created_at=datetime(2026, 8, 20, 11, 0, 0, tzinfo=timezone.utc),
        expected_date=date(2026, 8, 18),
        total_amount=5000.0,
        items=[PurchaseOrderItem(id="poi-3", po_id="po-3", product_id="p-1", qty_ordered=50.0, qty_received=45.0, unit_cost=100.0)],
    )

    po_repo = InMemoryPurchaseOrderRepository(pos=[po1, po2, po3])
    ret_repo = InMemoryPurchaseReturnRepository()

    service = SupplierPerformanceService(sup_repo, po_repo, ret_repo)
    resp = service.get_supplier_performance(as_of=now)

    assert len(resp.items) == 1
    sup_item = resp.items[0]

    # Hand-computed checks:
    # On-time: 2 out of 3 = 66.7%
    assert sup_item.on_time_delivery_pct == 66.7
    # Accuracy: (100 + 150 + 45) / (100 + 150 + 50) = 295 / 300 = 98.3%
    assert sup_item.fulfillment_accuracy_pct == 98.3
    # Return rate: 0 / 295 = 0.0%
    assert sup_item.return_rate_pct == 0.0
    # Total spend: 10000 + 15000 + 5000 = 30000.0
    assert sup_item.total_spend_inr == 30000.0
    # Rating band: On-time is 66.7% (<75%) -> needs_improvement
    assert sup_item.rating_band == "needs_improvement"


def test_retailer_churn_risk_heuristic_flag():
    """QA Item 2: A retailer manually given a large order-gap correctly surfaces the churn-risk flag."""
    now = datetime(2026, 8, 24, 12, 0, 0, tzinfo=timezone.utc)
    ret1 = Retailer(id="ret-active", name="Green Valley Mart", pricing_tier="gold")
    ret2 = Retailer(id="ret-churn", name="Stagnant Stores", pricing_tier="silver")

    ret_repo = InMemoryRetailerRepository([ret1, ret2])

    # Retailer 1: Active, orders every 10 days, last order 5 days ago (Avg gap: 10d, Days since last: 5d <= 20d -> NO CHURN RISK)
    so1_1 = SalesOrder(id="so-1", retailer_id="ret-active", order_date=datetime(2026, 8, 4, 10, 0, 0, tzinfo=timezone.utc), total_amount=5000.0, status=SOStatusEnum.DELIVERED)
    so1_2 = SalesOrder(id="so-2", retailer_id="ret-active", order_date=datetime(2026, 8, 14, 10, 0, 0, tzinfo=timezone.utc), total_amount=6000.0, status=SOStatusEnum.DELIVERED)
    so1_3 = SalesOrder(id="so-3", retailer_id="ret-active", order_date=datetime(2026, 8, 19, 10, 0, 0, tzinfo=timezone.utc), total_amount=7000.0, status=SOStatusEnum.DELIVERED)

    # Retailer 2: Historically ordered every 7 days (June 1, June 8, June 15), but no order since June 15 (70 days ago) -> CHURN RISK
    so2_1 = SalesOrder(id="so-4", retailer_id="ret-churn", order_date=datetime(2026, 6, 1, 10, 0, 0, tzinfo=timezone.utc), total_amount=4000.0, status=SOStatusEnum.DELIVERED)
    so2_2 = SalesOrder(id="so-5", retailer_id="ret-churn", order_date=datetime(2026, 6, 8, 10, 0, 0, tzinfo=timezone.utc), total_amount=4000.0, status=SOStatusEnum.DELIVERED)
    so2_3 = SalesOrder(id="so-6", retailer_id="ret-churn", order_date=datetime(2026, 6, 15, 10, 0, 0, tzinfo=timezone.utc), total_amount=4000.0, status=SOStatusEnum.DELIVERED)

    so_repo = InMemorySalesOrderRepository([so1_1, so1_2, so1_3, so2_1, so2_2, so2_3])

    service = RetailerPerformanceService(ret_repo, so_repo)
    resp = service.get_retailer_performance(as_of=now)

    active_item = next(it for it in resp.items if it.retailer_id == "ret-active")
    churn_item = next(it for it in resp.items if it.retailer_id == "ret-churn")

    assert active_item.is_churn_risk is False
    assert churn_item.is_churn_risk is True
    assert "exceeds 2x historical average" in (churn_item.churn_risk_reason or "")
    assert resp.summary.churn_risk_count == 1


def test_shrinkage_manual_sum_calculation():
    """QA Item 3: Shrinkage total matches a manual sum of damage/loss adjustments for a test period."""
    now = datetime(2026, 8, 24, 12, 0, 0, tzinfo=timezone.utc)
    p1 = Product(id="p-1", name="Rice 25kg", sku="RICE-25", cost_price=1000.0, base_uom_id="uom-kg")
    p2 = Product(id="p-2", name="Mustard Oil 1L", sku="OIL-1L", cost_price=150.0, base_uom_id="uom-l")
    prod_repo = InMemoryProductRepository([p1, p2])

    wh = Warehouse(id="wh-1", name="Central Facility", is_active=True)
    batch1 = StockBatch(id="b-1", product_id="p-1", warehouse_id="wh-1", batch_no="B01", quantity=100.0)
    batch2 = StockBatch(id="b-2", product_id="p-2", warehouse_id="wh-1", batch_no="B02", quantity=200.0)
    stock_repo = InMemoryStockRepository(warehouses=[wh], products=[p1, p2], batches=[batch1, batch2])

    # Record 3 damage/loss adjustments in past 30 days:
    # 1. Product 1: 5 units damaged (cost 1000) -> 5 * 1000 = 5000 INR
    # 2. Product 1: 2 units discrepancy (cost 1000) -> 2 * 1000 = 2000 INR
    # 3. Product 2: 10 units leakage (cost 150) -> 10 * 150 = 1500 INR
    # Total units lost = 5 + 2 + 10 = 17 units
    # Total loss value = 5000 + 2000 + 1500 = 8500 INR
    stock_repo.record_stock_adjustment("p-1", "wh-1", "b-1", -5.0, "Damaged in transit", created_by="staff-1")
    stock_repo.record_stock_adjustment("p-1", "wh-1", "b-1", -2.0, "Physical audit discrepancy", created_by="staff-1")
    stock_repo.record_stock_adjustment("p-2", "wh-1", "b-2", -10.0, "Bottle leakage", created_by="staff-1")

    service = ShrinkageService(stock_repo, prod_repo)
    resp = service.get_shrinkage(group_by="product", period="30d", as_of=now)

    assert resp.summary.total_units_lost == 17.0
    assert resp.summary.total_shrinkage_value_inr == 8500.0
    assert resp.summary.damage_incidents_count == 3
    assert len(resp.items) == 2

    # Product 1 should be ranked #1 with 7000 INR loss (82.4% share)
    p1_item = resp.items[0]
    assert p1_item.id == "p-1"
    assert p1_item.shrinkage_value_inr == 7000.0
    assert p1_item.units_lost == 7.0
    assert p1_item.pct_of_total_shrinkage == 82.4


def test_warehouse_breakdown_analytics():
    """Test WarehouseAnalyticsService calculations."""
    now = datetime(2026, 8, 24, 12, 0, 0, tzinfo=timezone.utc)
    p1 = Product(id="p-1", name="Rice 25kg", sku="RICE-25", cost_price=1000.0)
    p2 = Product(id="p-2", name="Wheat 50kg", sku="WHEAT-50", cost_price=1500.0)
    prod_repo = InMemoryProductRepository([p1, p2])

    wh1 = Warehouse(id="wh-1", name="Central Hub", location="Mumbai", is_active=True)
    wh2 = Warehouse(id="wh-2", name="North Depot", location="Delhi", is_active=True)

    b1 = StockBatch(id="b-1", product_id="p-1", warehouse_id="wh-1", batch_no="B01", quantity=50.0) # 50 * 1000 = 50,000 INR
    b2 = StockBatch(id="b-2", product_id="p-2", warehouse_id="wh-2", batch_no="B02", quantity=20.0) # 20 * 1500 = 30,000 INR

    stock_repo = InMemoryStockRepository(warehouses=[wh1, wh2], products=[p1, p2], batches=[b1, b2])

    service = WarehouseAnalyticsService(stock_repo, prod_repo)
    resp = service.get_warehouse_breakdown(as_of=now)

    assert resp.summary.total_warehouses == 2
    assert resp.summary.company_total_stock_units == 70.0
    assert resp.summary.company_total_valuation_inr == 80000.0

    wh1_item = next(w for w in resp.warehouses if w.warehouse_id == "wh-1")
    assert wh1_item.total_stock_value_inr == 50000.0
    assert wh1_item.valuation_share_pct == 62.5


def test_fastapi_endpoints_step_16_2():
    """Test the 4 FastAPI router endpoints for Step 16.2."""
    from app.core.di import (
        get_retailer_performance_service,
        get_shrinkage_service,
        get_supplier_performance_service,
        get_warehouse_analytics_service,
    )

    admin_user = Profile(id="admin-user", email="owner@wareflow.local", role="owner", is_active=True)
    app.dependency_overrides[get_current_user] = lambda: admin_user

    p1 = Product(id="p-1", name="Rice 25kg", sku="RICE-25", cost_price=1000.0)
    wh1 = Warehouse(id="wh-1", name="Central Facility", is_active=True)
    b1 = StockBatch(id="b-1", product_id="p-1", warehouse_id="wh-1", batch_no="B01", quantity=100.0)
    sup1 = Supplier(id="sup-1", name="Apex FMCG", is_active=True)
    ret1 = Retailer(id="ret-1", name="Green Valley Mart", pricing_tier="gold")

    prod_repo = InMemoryProductRepository([p1])
    stock_repo = InMemoryStockRepository(warehouses=[wh1], products=[p1], batches=[b1])
    sup_repo = InMemorySupplierRepository([sup1])
    po_repo = InMemoryPurchaseOrderRepository([])
    ret_repo = InMemoryPurchaseReturnRepository()
    retailer_repo = InMemoryRetailerRepository([ret1])
    so_repo = InMemorySalesOrderRepository([])

    app.dependency_overrides[get_supplier_performance_service] = lambda: SupplierPerformanceService(sup_repo, po_repo, ret_repo)
    app.dependency_overrides[get_retailer_performance_service] = lambda: RetailerPerformanceService(retailer_repo, so_repo)
    app.dependency_overrides[get_warehouse_analytics_service] = lambda: WarehouseAnalyticsService(stock_repo, prod_repo)
    app.dependency_overrides[get_shrinkage_service] = lambda: ShrinkageService(stock_repo, prod_repo)

    client = TestClient(app)

    # 1. Supplier performance
    resp_sup = client.get("/analytics/supplier-performance")
    assert resp_sup.status_code == 200
    data_sup = resp_sup.json()
    assert "summary" in data_sup
    assert "items" in data_sup

    # 2. Retailer performance
    resp_ret = client.get("/analytics/retailer-performance")
    assert resp_ret.status_code == 200
    data_ret = resp_ret.json()
    assert "summary" in data_ret
    assert "items" in data_ret

    # 3. Warehouse breakdown
    resp_wh = client.get("/analytics/warehouse-breakdown")
    assert resp_wh.status_code == 200
    data_wh = resp_wh.json()
    assert "summary" in data_wh
    assert "warehouses" in data_wh

    # 4. Shrinkage
    resp_sh = client.get("/analytics/shrinkage?group_by=product&period=30d")
    assert resp_sh.status_code == 200
    data_sh = resp_sh.json()
    assert "summary" in data_sh
    assert "items" in data_sh

    app.dependency_overrides.clear()

