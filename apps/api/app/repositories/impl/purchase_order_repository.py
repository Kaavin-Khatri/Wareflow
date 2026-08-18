"""SQLAlchemy and InMemory implementations of PurchaseOrderRepositoryInterface."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.supplier import POStatusEnum, PurchaseOrder, PurchaseOrderItem
from app.repositories.interfaces.purchase_order_repository import PurchaseOrderRepositoryInterface


class SqlAlchemyPurchaseOrderRepository(PurchaseOrderRepositoryInterface):
    """SQLAlchemy implementation of purchase order data access."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def _base_query(self):
        return select(PurchaseOrder).options(
            joinedload(PurchaseOrder.supplier),
            selectinload(PurchaseOrder.items).joinedload(PurchaseOrderItem.product),
            selectinload(PurchaseOrder.items).joinedload(PurchaseOrderItem.uom),
        )

    def get_by_id(self, po_id: str) -> PurchaseOrder | None:
        stmt = self._base_query().where(PurchaseOrder.id == po_id)
        return self.session.scalars(stmt).unique().first()

    def get_by_po_number(self, po_number: str) -> PurchaseOrder | None:
        stmt = self._base_query().where(PurchaseOrder.po_number == po_number.strip().upper())
        return self.session.scalars(stmt).unique().first()

    def list_purchase_orders(
        self,
        supplier_id: str | None = None,
        status: str | None = None,
        search: str | None = None,
    ) -> list[PurchaseOrder]:
        stmt = self._base_query()

        if supplier_id:
            stmt = stmt.where(PurchaseOrder.supplier_id == supplier_id)

        if status:
            try:
                enum_status = POStatusEnum(status.lower())
                stmt = stmt.where(PurchaseOrder.status == enum_status)
            except ValueError:
                pass

        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    PurchaseOrder.po_number.ilike(term),
                    PurchaseOrder.supplier.has(
                        func.lower(
                            func.coalesce(PurchaseOrder.supplier.property.mapper.class_.name, "")
                        ).like(term.lower())
                    ),
                )
            )

        stmt = stmt.order_by(PurchaseOrder.created_at.desc())
        return list(self.session.scalars(stmt).unique().all())

    def generate_next_po_number(self) -> str:
        prefix = datetime.now().strftime("PO-%Y%m")
        count_stmt = select(func.count(PurchaseOrder.id)).where(
            PurchaseOrder.po_number.like(f"{prefix}%")
        )
        count = self.session.scalar(count_stmt) or 0
        return f"{prefix}-{(count + 1):04d}"

    def create_purchase_order(
        self, po_data: dict[str, Any], items_data: list[dict[str, Any]]
    ) -> PurchaseOrder:
        po_number = po_data.get("po_number") or self.generate_next_po_number()

        total_amount = sum(
            float(item["qty_ordered"]) * float(item["unit_cost"]) for item in items_data
        )

        po = PurchaseOrder(
            id=po_data.get("id") or str(uuid.uuid4()),
            po_number=po_number,
            supplier_id=po_data["supplier_id"],
            status=po_data.get("status", POStatusEnum.DRAFT),
            order_date=po_data.get("order_date") or datetime.now(),
            expected_date=po_data.get("expected_date"),
            total_amount=round(total_amount, 2),
        )
        self.session.add(po)
        self.session.flush()

        for item in items_data:
            po_item = PurchaseOrderItem(
                id=item.get("id") or str(uuid.uuid4()),
                po_id=po.id,
                product_id=item["product_id"],
                qty_ordered=float(item["qty_ordered"]),
                qty_received=float(item.get("qty_received", 0.0)),
                unit_cost=float(item["unit_cost"]),
                uom_id=item.get("uom_id"),
            )
            self.session.add(po_item)

        self.session.commit()
        return self.get_by_id(po.id) or po

    def update_purchase_order(
        self,
        po_id: str,
        po_data: dict[str, Any],
        items_data: list[dict[str, Any]] | None = None,
    ) -> PurchaseOrder | None:
        po = self.get_by_id(po_id)
        if not po:
            return None

        if "supplier_id" in po_data and po_data["supplier_id"]:
            po.supplier_id = po_data["supplier_id"]
        if "expected_date" in po_data:
            po.expected_date = po_data["expected_date"]
        if "status" in po_data and po_data["status"]:
            po.status = po_data["status"]

        if items_data is not None:
            # Remove old items and replace with new set
            for old_item in list(po.items):
                self.session.delete(old_item)
            self.session.flush()

            total_amount = 0.0
            for item in items_data:
                item_total = float(item["qty_ordered"]) * float(item["unit_cost"])
                total_amount += item_total
                new_item = PurchaseOrderItem(
                    id=item.get("id") or str(uuid.uuid4()),
                    po_id=po.id,
                    product_id=item["product_id"],
                    qty_ordered=float(item["qty_ordered"]),
                    qty_received=float(item.get("qty_received", 0.0)),
                    unit_cost=float(item["unit_cost"]),
                    uom_id=item.get("uom_id"),
                )
                self.session.add(new_item)
            po.total_amount = round(total_amount, 2)

        self.session.commit()
        return self.get_by_id(po.id)

    def update_status(self, po_id: str, status: POStatusEnum) -> PurchaseOrder | None:
        po = self.session.get(PurchaseOrder, po_id)
        if not po:
            return None
        po.status = status
        self.session.commit()
        return self.get_by_id(po_id)

    def update_item_received_qty(
        self, item_id: str, additional_qty: float
    ) -> PurchaseOrderItem | None:
        item = self.session.get(PurchaseOrderItem, item_id)
        if not item:
            return None
        item.qty_received = round(float(item.qty_received) + additional_qty, 2)
        self.session.flush()
        return item


class InMemoryPurchaseOrderRepository(PurchaseOrderRepositoryInterface):
    """In-memory mock implementation for high-speed unit testing."""

    def __init__(self, pos: list[PurchaseOrder] | None = None) -> None:
        self.pos: dict[str, PurchaseOrder] = {po.id: po for po in (pos or [])}

    def get_by_id(self, po_id: str) -> PurchaseOrder | None:
        return self.pos.get(po_id)

    def get_by_po_number(self, po_number: str) -> PurchaseOrder | None:
        clean = po_number.strip().upper()
        for po in self.pos.values():
            if po.po_number.upper() == clean:
                return po
        return None

    def list_purchase_orders(
        self,
        supplier_id: str | None = None,
        status: str | None = None,
        search: str | None = None,
    ) -> list[PurchaseOrder]:
        results = list(self.pos.values())

        if supplier_id:
            results = [po for po in results if po.supplier_id == supplier_id]

        if status:
            try:
                enum_status = POStatusEnum(status.lower())
                results = [po for po in results if po.status == enum_status]
            except ValueError:
                pass

        if search:
            term = search.strip().lower()
            results = [
                po
                for po in results
                if term in po.po_number.lower()
                or (po.supplier and term in po.supplier.name.lower())
            ]

        results.sort(
            key=lambda p: p.created_at if hasattr(p, "created_at") else datetime.now(), reverse=True
        )
        return results

    def generate_next_po_number(self) -> str:
        prefix = datetime.now().strftime("PO-%Y%m")
        count = sum(1 for po in self.pos.values() if po.po_number.startswith(prefix))
        return f"{prefix}-{(count + 1):04d}"

    def create_purchase_order(
        self, po_data: dict[str, Any], items_data: list[dict[str, Any]]
    ) -> PurchaseOrder:
        po_id = po_data.get("id") or str(uuid.uuid4())
        po_number = po_data.get("po_number") or self.generate_next_po_number()

        total_amount = sum(
            float(item["qty_ordered"]) * float(item["unit_cost"]) for item in items_data
        )

        po = PurchaseOrder(
            id=po_id,
            po_number=po_number,
            supplier_id=po_data["supplier_id"],
            status=po_data.get("status", POStatusEnum.DRAFT),
            order_date=po_data.get("order_date") or datetime.now(),
            expected_date=po_data.get("expected_date"),
            total_amount=round(total_amount, 2),
            created_at=datetime.now(),
        )
        po.items = []

        for item in items_data:
            po_item = PurchaseOrderItem(
                id=item.get("id") or str(uuid.uuid4()),
                po_id=po.id,
                product_id=item["product_id"],
                qty_ordered=float(item["qty_ordered"]),
                qty_received=float(item.get("qty_received", 0.0)),
                unit_cost=float(item["unit_cost"]),
                uom_id=item.get("uom_id"),
            )
            po.items.append(po_item)

        self.pos[po_id] = po
        return po

    def update_purchase_order(
        self,
        po_id: str,
        po_data: dict[str, Any],
        items_data: list[dict[str, Any]] | None = None,
    ) -> PurchaseOrder | None:
        po = self.get_by_id(po_id)
        if not po:
            return None

        if "supplier_id" in po_data and po_data["supplier_id"]:
            po.supplier_id = po_data["supplier_id"]
        if "expected_date" in po_data:
            po.expected_date = po_data["expected_date"]
        if "status" in po_data and po_data["status"]:
            po.status = po_data["status"]

        if items_data is not None:
            po.items = []
            total_amount = 0.0
            for item in items_data:
                total_amount += float(item["qty_ordered"]) * float(item["unit_cost"])
                po_item = PurchaseOrderItem(
                    id=item.get("id") or str(uuid.uuid4()),
                    po_id=po.id,
                    product_id=item["product_id"],
                    qty_ordered=float(item["qty_ordered"]),
                    qty_received=float(item.get("qty_received", 0.0)),
                    unit_cost=float(item["unit_cost"]),
                    uom_id=item.get("uom_id"),
                )
                po.items.append(po_item)
            po.total_amount = round(total_amount, 2)

        return po

    def update_status(self, po_id: str, status: POStatusEnum) -> PurchaseOrder | None:
        po = self.get_by_id(po_id)
        if not po:
            return None
        po.status = status
        return po

    def update_item_received_qty(
        self, item_id: str, additional_qty: float
    ) -> PurchaseOrderItem | None:
        for po in self.pos.values():
            for item in po.items:
                if item.id == item_id:
                    item.qty_received = round(float(item.qty_received) + additional_qty, 2)
                    return item
        return None
