from datetime import datetime
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.catalog import Category, Product
from app.models.supplier import POStatusEnum, PurchaseOrder, PurchaseOrderItem, Supplier
from app.models.warehouse import StockBatch, Warehouse
from app.repositories.interfaces.stock_analytics_repository import (
    StockAnalyticsRepositoryInterface,
)


class SqlAlchemyStockAnalyticsRepository(StockAnalyticsRepositoryInterface):
    """SQLAlchemy implementation of StockAnalyticsRepositoryInterface."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_stock_valuation_data(self) -> list[dict[str, Any]]:
        """Fetch joined batches with product cost_price, category, and warehouse info."""
        results = (
            self.session.query(
                StockBatch.id.label("batch_id"),
                StockBatch.batch_no,
                StockBatch.quantity,
                StockBatch.warehouse_id,
                Warehouse.name.label("warehouse_name"),
                Product.id.label("product_id"),
                Product.sku,
                Product.name.label("product_name"),
                Product.cost_price,
                Product.category_id,
                Category.name.label("category_name"),
            )
            .join(Product, StockBatch.product_id == Product.id)
            .join(Warehouse, StockBatch.warehouse_id == Warehouse.id)
            .outerjoin(Category, Product.category_id == Category.id)
            .filter(StockBatch.quantity > 0, Product.is_active.is_(True))
            .all()
        )
        rows: list[dict[str, Any]] = []
        for r in results:
            d = r._asdict()
            d["quantity"] = float(d["quantity"])
            d["cost_price"] = float(d["cost_price"] or 0.0)
            rows.append(d)
        return rows

    def get_health_distribution_data(self) -> list[dict[str, Any]]:
        """Fetch active products with reorder_points and on-hand totals."""
        products = (
            self.session.query(Product)
            .filter(Product.is_active.is_(True))
            .options(joinedload(Product.category))
            .all()
        )
        on_hand_subq = dict(
            self.session.query(
                StockBatch.product_id,
                func.coalesce(func.sum(StockBatch.quantity), 0.0),
            )
            .group_by(StockBatch.product_id)
            .all()
        )
        rows: list[dict[str, Any]] = []
        for p in products:
            on_hand = float(on_hand_subq.get(p.id, 0.0))
            rows.append(
                {
                    "product_id": p.id,
                    "sku": p.sku,
                    "name": p.name,
                    "reorder_point": p.reorder_point or 0,
                    "total_on_hand": on_hand,
                }
            )
        return rows

    def get_top_products_data(self) -> list[dict[str, Any]]:
        """Fetch active products with total on-hand, cost_price, and base unit."""
        products = (
            self.session.query(Product)
            .filter(Product.is_active.is_(True))
            .options(
                joinedload(Product.category),
                joinedload(Product.base_uom),
            )
            .all()
        )
        on_hand_subq = dict(
            self.session.query(
                StockBatch.product_id,
                func.coalesce(func.sum(StockBatch.quantity), 0.0),
            )
            .group_by(StockBatch.product_id)
            .all()
        )
        rows: list[dict[str, Any]] = []
        for p in products:
            on_hand = float(on_hand_subq.get(p.id, 0.0))
            cost = float(p.cost_price or 0.0)
            rows.append(
                {
                    "product_id": p.id,
                    "sku": p.sku,
                    "name": p.name,
                    "category_name": p.category.name if p.category else "Uncategorized",
                    "total_on_hand": on_hand,
                    "cost_price": cost,
                    "total_value": round(on_hand * cost, 2),
                    "base_uom_name": p.base_uom.name if p.base_uom else "Units",
                }
            )
        return rows

    def get_batch_expiry_data(self) -> list[dict[str, Any]]:
        """Fetch all positive stock batches with product cost and expiry dates."""
        results = (
            self.session.query(
                StockBatch.id.label("batch_id"),
                StockBatch.batch_no,
                StockBatch.quantity,
                StockBatch.expiry_date,
                Product.cost_price,
            )
            .join(Product, StockBatch.product_id == Product.id)
            .filter(StockBatch.quantity > 0, Product.is_active.is_(True))
            .all()
        )
        rows: list[dict[str, Any]] = []
        for r in results:
            d = r._asdict()
            d["quantity"] = float(d["quantity"])
            d["cost_price"] = float(d["cost_price"] or 0.0)
            rows.append(d)
        return rows

    # --- Step 6.2: Purchasing Spend Implementations ---

    def get_spend_trend_data(self, months: int = 12) -> list[dict[str, Any]]:
        """Fetch received purchase order line items."""
        results = (
            self.session.query(
                PurchaseOrder.id.label("po_id"),
                PurchaseOrder.po_number,
                PurchaseOrder.order_date,
                PurchaseOrderItem.qty_received,
                PurchaseOrderItem.qty_ordered,
                PurchaseOrderItem.unit_cost,
            )
            .join(PurchaseOrder, PurchaseOrderItem.po_id == PurchaseOrder.id)
            .filter(
                PurchaseOrder.status.in_([POStatusEnum.RECEIVED, POStatusEnum.PARTIALLY_RECEIVED])
                | (PurchaseOrderItem.qty_received > 0)
            )
            .all()
        )
        rows: list[dict[str, Any]] = []
        for r in results:
            d = r._asdict()
            qty = float(
                d["qty_received"] if float(d["qty_received"] or 0.0) > 0 else d["qty_ordered"]
            )
            d["qty_received"] = qty
            d["unit_cost"] = float(d["unit_cost"] or 0.0)
            rows.append(d)
        return rows

    def get_spend_by_supplier_data(self, months: int = 12) -> list[dict[str, Any]]:
        """Fetch received items grouped by supplier."""
        results = (
            self.session.query(
                Supplier.id.label("supplier_id"),
                Supplier.name.label("supplier_name"),
                PurchaseOrder.id.label("po_id"),
                PurchaseOrderItem.qty_received,
                PurchaseOrderItem.qty_ordered,
                PurchaseOrderItem.unit_cost,
            )
            .join(PurchaseOrder, PurchaseOrderItem.po_id == PurchaseOrder.id)
            .join(Supplier, PurchaseOrder.supplier_id == Supplier.id)
            .filter(
                PurchaseOrder.status.in_([POStatusEnum.RECEIVED, POStatusEnum.PARTIALLY_RECEIVED])
                | (PurchaseOrderItem.qty_received > 0)
            )
            .all()
        )
        rows: list[dict[str, Any]] = []
        for r in results:
            d = r._asdict()
            qty = float(
                d["qty_received"] if float(d["qty_received"] or 0.0) > 0 else d["qty_ordered"]
            )
            d["qty_received"] = qty
            d["unit_cost"] = float(d["unit_cost"] or 0.0)
            rows.append(d)
        return rows

    def get_spend_by_category_data(self, months: int = 12) -> list[dict[str, Any]]:
        """Fetch received items grouped by product category."""
        results = (
            self.session.query(
                Category.id.label("category_id"),
                Category.name.label("category_name"),
                PurchaseOrderItem.qty_received,
                PurchaseOrderItem.qty_ordered,
                PurchaseOrderItem.unit_cost,
            )
            .join(Product, PurchaseOrderItem.product_id == Product.id)
            .join(PurchaseOrder, PurchaseOrderItem.po_id == PurchaseOrder.id)
            .outerjoin(Category, Product.category_id == Category.id)
            .filter(
                PurchaseOrder.status.in_([POStatusEnum.RECEIVED, POStatusEnum.PARTIALLY_RECEIVED])
                | (PurchaseOrderItem.qty_received > 0)
            )
            .all()
        )
        rows: list[dict[str, Any]] = []
        for r in results:
            d = r._asdict()
            qty = float(
                d["qty_received"] if float(d["qty_received"] or 0.0) > 0 else d["qty_ordered"]
            )
            d["category_name"] = d["category_name"] or "Uncategorized"
            d["qty_received"] = qty
            d["unit_cost"] = float(d["unit_cost"] or 0.0)
            rows.append(d)
        return rows

    def get_product_cost_history_data(
        self, product_ids: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Fetch historical purchase order unit costs and baseline costs per product."""
        query = self.session.query(Product).filter(Product.is_active.is_(True))
        if product_ids:
            query = query.filter(Product.id.in_(product_ids))
        products = query.all()

        po_items = (
            self.session.query(
                PurchaseOrderItem.product_id,
                PurchaseOrderItem.unit_cost,
                PurchaseOrder.order_date,
            )
            .join(PurchaseOrder, PurchaseOrderItem.po_id == PurchaseOrder.id)
            .order_by(PurchaseOrder.order_date.asc())
            .all()
        )

        history_by_prod: dict[str, list[dict[str, Any]]] = {}
        for item in po_items:
            history_by_prod.setdefault(item.product_id, []).append(
                {
                    "recorded_at": item.order_date.isoformat()
                    if hasattr(item.order_date, "isoformat")
                    else str(item.order_date),
                    "cost_price": float(item.unit_cost or 0.0),
                    "source": "PO",
                }
            )

        rows: list[dict[str, Any]] = []
        for p in products:
            pts = history_by_prod.get(p.id, [])
            base_cost = float(p.cost_price or 0.0)
            if not pts:
                pts = [
                    {
                        "recorded_at": p.created_at.isoformat()
                        if hasattr(p.created_at, "isoformat")
                        else str(p.created_at),
                        "cost_price": base_cost,
                        "source": "Base",
                    }
                ]
            rows.append(
                {
                    "product_id": p.id,
                    "sku": p.sku,
                    "name": p.name,
                    "current_cost_price": base_cost,
                    "cost_points": pts,
                }
            )
        return rows


class InMemoryStockAnalyticsRepository(StockAnalyticsRepositoryInterface):
    """In-memory test double for StockAnalyticsRepositoryInterface."""

    def __init__(
        self,
        products: list[dict[str, Any]] | None = None,
        categories: list[dict[str, Any]] | None = None,
        warehouses: list[dict[str, Any]] | None = None,
        batches: list[dict[str, Any]] | None = None,
        suppliers: list[dict[str, Any]] | None = None,
        purchase_orders: list[dict[str, Any]] | None = None,
        purchase_order_items: list[dict[str, Any]] | None = None,
    ) -> None:
        self.products = {p["id"]: p for p in (products or [])}
        self.categories = {c["id"]: c for c in (categories or [])}
        self.warehouses = {w["id"]: w for w in (warehouses or [])}
        self.batches = {b["id"]: b for b in (batches or [])}
        self.suppliers = {s["id"]: s for s in (suppliers or [])}
        self.purchase_orders = {po["id"]: po for po in (purchase_orders or [])}
        self.purchase_order_items = purchase_order_items or []

    def get_stock_valuation_data(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for b in self.batches.values():
            qty = float(b.get("quantity", 0.0))
            if qty <= 0:
                continue
            prod = self.products.get(b.get("product_id"))
            if not prod or not prod.get("is_active", True):
                continue
            wh = self.warehouses.get(b.get("warehouse_id"), {})
            cat = self.categories.get(prod.get("category_id"), {})
            rows.append(
                {
                    "batch_id": b["id"],
                    "batch_no": b.get("batch_no", ""),
                    "quantity": qty,
                    "warehouse_id": b.get("warehouse_id", ""),
                    "warehouse_name": wh.get("name", "Unknown Warehouse"),
                    "product_id": prod["id"],
                    "sku": prod.get("sku", ""),
                    "product_name": prod.get("name", ""),
                    "cost_price": float(prod.get("cost_price", 0.0)),
                    "category_id": prod.get("category_id"),
                    "category_name": cat.get("name", "Uncategorized"),
                }
            )
        return rows

    def get_health_distribution_data(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for prod in self.products.values():
            if not prod.get("is_active", True):
                continue
            pid = prod["id"]
            on_hand = sum(
                float(b.get("quantity", 0.0))
                for b in self.batches.values()
                if b.get("product_id") == pid
            )
            rows.append(
                {
                    "product_id": pid,
                    "sku": prod.get("sku", ""),
                    "name": prod.get("name", ""),
                    "reorder_point": prod.get("reorder_point", 0),
                    "total_on_hand": on_hand,
                }
            )
        return rows

    def get_top_products_data(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for prod in self.products.values():
            if not prod.get("is_active", True):
                continue
            pid = prod["id"]
            on_hand = sum(
                float(b.get("quantity", 0.0))
                for b in self.batches.values()
                if b.get("product_id") == pid
            )
            cost = float(prod.get("cost_price", 0.0))
            cat = self.categories.get(prod.get("category_id"), {})
            rows.append(
                {
                    "product_id": pid,
                    "sku": prod.get("sku", ""),
                    "name": prod.get("name", ""),
                    "category_name": cat.get("name", "Uncategorized"),
                    "total_on_hand": on_hand,
                    "cost_price": cost,
                    "total_value": round(on_hand * cost, 2),
                    "base_uom_name": prod.get("base_uom_name", "Units"),
                }
            )
        return rows

    def get_batch_expiry_data(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for b in self.batches.values():
            qty = float(b.get("quantity", 0.0))
            if qty <= 0:
                continue
            prod = self.products.get(b.get("product_id"))
            if not prod or not prod.get("is_active", True):
                continue
            rows.append(
                {
                    "batch_id": b["id"],
                    "batch_no": b.get("batch_no", ""),
                    "quantity": qty,
                    "expiry_date": b.get("expiry_date"),
                    "cost_price": float(prod.get("cost_price", 0.0)),
                }
            )
        return rows

    def get_spend_trend_data(self, months: int = 12) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for item in self.purchase_order_items:
            po = self.purchase_orders.get(item.get("po_id"), {})
            qty = float(item.get("qty_received", 0.0))
            if qty <= 0 and po.get("status") in ["received", "partially_received"]:
                qty = float(item.get("qty_ordered", 0.0))
            if qty > 0:
                rows.append(
                    {
                        "po_id": po.get("id"),
                        "po_number": po.get("po_number"),
                        "order_date": po.get("order_date") or datetime.now(),
                        "qty_received": qty,
                        "unit_cost": float(item.get("unit_cost", 0.0)),
                    }
                )
        return rows

    def get_spend_by_supplier_data(self, months: int = 12) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for item in self.purchase_order_items:
            po = self.purchase_orders.get(item.get("po_id"), {})
            sup = self.suppliers.get(po.get("supplier_id"), {})
            qty = float(item.get("qty_received", 0.0))
            if qty <= 0 and po.get("status") in ["received", "partially_received"]:
                qty = float(item.get("qty_ordered", 0.0))
            if qty > 0:
                rows.append(
                    {
                        "supplier_id": sup.get("id", po.get("supplier_id", "unknown")),
                        "supplier_name": sup.get("name", "Unknown Supplier"),
                        "po_id": po.get("id"),
                        "qty_received": qty,
                        "unit_cost": float(item.get("unit_cost", 0.0)),
                    }
                )
        return rows

    def get_spend_by_category_data(self, months: int = 12) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for item in self.purchase_order_items:
            po = self.purchase_orders.get(item.get("po_id"), {})
            prod = self.products.get(item.get("product_id"), {})
            cat = self.categories.get(prod.get("category_id"), {})
            qty = float(item.get("qty_received", 0.0))
            if qty <= 0 and po.get("status") in ["received", "partially_received"]:
                qty = float(item.get("qty_ordered", 0.0))
            if qty > 0:
                rows.append(
                    {
                        "category_id": cat.get("id"),
                        "category_name": cat.get("name", "Uncategorized"),
                        "qty_received": qty,
                        "unit_cost": float(item.get("unit_cost", 0.0)),
                    }
                )
        return rows

    def get_product_cost_history_data(
        self, product_ids: list[str] | None = None
    ) -> list[dict[str, Any]]:
        prods = list(self.products.values())
        if product_ids:
            prods = [p for p in prods if p.get("id") in product_ids]

        history_by_prod: dict[str, list[dict[str, Any]]] = {}
        for item in self.purchase_order_items:
            po = self.purchase_orders.get(item.get("po_id"), {})
            pid = item.get("product_id")
            od = po.get("order_date") or datetime.now()
            history_by_prod.setdefault(pid, []).append(
                {
                    "recorded_at": od.isoformat() if hasattr(od, "isoformat") else str(od),
                    "cost_price": float(item.get("unit_cost", 0.0)),
                    "source": "PO",
                }
            )

        rows: list[dict[str, Any]] = []
        for p in prods:
            pts = history_by_prod.get(p["id"], [])
            base_cost = float(p.get("cost_price", 0.0))
            if not pts:
                pts = [
                    {
                        "recorded_at": str(p.get("created_at", datetime.now().isoformat())),
                        "cost_price": base_cost,
                        "source": "Base",
                    }
                ]
            rows.append(
                {
                    "product_id": p["id"],
                    "sku": p.get("sku", ""),
                    "name": p.get("name", ""),
                    "current_cost_price": base_cost,
                    "cost_points": pts,
                }
            )
        return rows
