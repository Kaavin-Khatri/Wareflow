"""SQLAlchemy and InMemory implementations of RecallRepositoryInterface."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.catalog import Product
from app.models.inventory import StockMovement, StockMovementTypeEnum
from app.models.portal import Customer
from app.models.recalls import (
    BatchRecall,
    RecallAffectedOrder,
    RecallSeverityEnum,
    RecallStatusEnum,
)
from app.models.retailer import Retailer, SalesOrder
from app.models.warehouse import StockBatch, Warehouse
from app.repositories.interfaces.recall_repository import RecallRepositoryInterface


class SqlAlchemyRecallRepository(RecallRepositoryInterface):
    """Production SQLAlchemy repository for batch recall traceability."""

    def __init__(self, session: Session):
        self.session = session

    def create_recall(
        self,
        batch_id: str,
        product_id: str,
        reason: str,
        severity: RecallSeverityEnum = RecallSeverityEnum.MEDIUM,
    ) -> BatchRecall:
        recall = BatchRecall(
            id=str(uuid.uuid4()),
            batch_id=batch_id,
            product_id=product_id,
            reason=reason,
            severity=severity,
            status=RecallStatusEnum.INITIATED,
            initiated_at=datetime.now(UTC),
        )
        self.session.add(recall)
        self.session.commit()
        self.session.refresh(recall)
        return recall

    def find_affected_orders_by_batch(self, batch_id: str) -> list[dict[str, Any]]:
        stmt = (
            select(
                StockMovement.reference_id.label("sales_order_id"),
                SalesOrder.buyer_type,
                SalesOrder.retailer_id,
                SalesOrder.customer_id,
                Retailer.name.label("retailer_name"),
                Retailer.phone.label("retailer_phone"),
                Retailer.email.label("retailer_email"),
                Customer.name.label("customer_name"),
                Customer.phone.label("customer_phone"),
                Customer.email.label("customer_email"),
                SalesOrder.created_at.label("order_date"),
                func.sum(func.abs(StockMovement.quantity)).label("quantity_supplied"),
            )
            .join(SalesOrder, SalesOrder.id == StockMovement.reference_id)
            .outerjoin(Retailer, Retailer.id == SalesOrder.retailer_id)
            .outerjoin(Customer, Customer.id == SalesOrder.customer_id)
            .where(
                StockMovement.batch_id == batch_id,
                StockMovement.type == StockMovementTypeEnum.OUT,
                StockMovement.reference_type == "sales_order",
            )
            .group_by(
                StockMovement.reference_id,
                SalesOrder.buyer_type,
                SalesOrder.retailer_id,
                SalesOrder.customer_id,
                Retailer.name,
                Retailer.phone,
                Retailer.email,
                Customer.name,
                Customer.phone,
                Customer.email,
                SalesOrder.created_at,
            )
        )

        rows = self.session.execute(stmt).mappings().all()
        results: list[dict[str, Any]] = []

        for r in rows:
            b_type = (
                r["buyer_type"].value
                if hasattr(r["buyer_type"], "value")
                else str(r["buyer_type"] or "retailer")
            )
            if b_type == "retailer":
                buyer_name = r["retailer_name"] or "Unknown Retailer"
                buyer_phone = r["retailer_phone"]
                buyer_email = r["retailer_email"]
                buyer_id = r["retailer_id"]
            else:
                buyer_name = r["customer_name"] or "Walk-in Customer"
                buyer_phone = r["customer_phone"]
                buyer_email = r["customer_email"]
                buyer_id = r["customer_id"]

            results.append(
                {
                    "sales_order_id": r["sales_order_id"],
                    "sales_order_number": r["sales_order_id"],
                    "buyer_type": b_type,
                    "buyer_id": buyer_id,
                    "retailer_id": r["retailer_id"],
                    "customer_id": r["customer_id"],
                    "buyer_name": buyer_name,
                    "buyer_phone": buyer_phone,
                    "buyer_email": buyer_email,
                    "order_date": r["order_date"],
                    "quantity_supplied": float(r["quantity_supplied"] or 0),
                }
            )

        return results

    def populate_affected_orders(
        self, recall_id: str, affected_orders_data: list[dict[str, Any]]
    ) -> list[RecallAffectedOrder]:
        records: list[RecallAffectedOrder] = []
        for item in affected_orders_data:
            rec = RecallAffectedOrder(
                id=str(uuid.uuid4()),
                recall_id=recall_id,
                sales_order_id=item["sales_order_id"],
                retailer_id=item.get("retailer_id"),
                customer_id=item.get("customer_id"),
                notified_at=None,
            )
            records.append(rec)

        if records:
            self.session.add_all(records)
            self.session.commit()
            for r in records:
                self.session.refresh(r)

        return records

    def get_recall_by_id(self, recall_id: str) -> BatchRecall | None:
        stmt = (
            select(BatchRecall)
            .options(
                joinedload(BatchRecall.product),
                joinedload(BatchRecall.batch).joinedload(StockBatch.warehouse),
                joinedload(BatchRecall.affected_orders).joinedload(RecallAffectedOrder.retailer),
                joinedload(BatchRecall.affected_orders).joinedload(RecallAffectedOrder.customer),
                joinedload(BatchRecall.affected_orders).joinedload(RecallAffectedOrder.sales_order),
            )
            .where(BatchRecall.id == recall_id)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_active_recall_for_batch(self, batch_id: str) -> BatchRecall | None:
        stmt = select(BatchRecall).where(
            BatchRecall.batch_id == batch_id,
            BatchRecall.status.in_([RecallStatusEnum.INITIATED, RecallStatusEnum.NOTIFYING]),
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_all_active_recalled_batch_ids(self) -> set[str]:
        stmt = select(BatchRecall.batch_id).where(
            BatchRecall.status.in_([RecallStatusEnum.INITIATED, RecallStatusEnum.NOTIFYING])
        )
        results = self.session.execute(stmt).scalars().all()
        return set(results)

    def list_recalls(
        self,
        page: int = 1,
        page_size: int = 50,
        status: str | None = None,
        severity: str | None = None,
        product_id: str | None = None,
        search: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        stmt = (
            select(
                BatchRecall.id,
                BatchRecall.batch_id,
                StockBatch.batch_no,
                BatchRecall.product_id,
                Product.name.label("product_name"),
                Product.sku.label("product_sku"),
                Warehouse.name.label("warehouse_name"),
                StockBatch.quantity.label("remaining_quantity"),
                BatchRecall.reason,
                BatchRecall.severity,
                BatchRecall.status,
                BatchRecall.initiated_at,
                BatchRecall.resolved_at,
                func.count(RecallAffectedOrder.id).label("affected_orders_count"),
                func.count(RecallAffectedOrder.notified_at).label("notified_count"),
            )
            .join(Product, Product.id == BatchRecall.product_id)
            .join(StockBatch, StockBatch.id == BatchRecall.batch_id)
            .join(Warehouse, Warehouse.id == StockBatch.warehouse_id)
            .outerjoin(RecallAffectedOrder, RecallAffectedOrder.recall_id == BatchRecall.id)
            .group_by(
                BatchRecall.id,
                BatchRecall.batch_id,
                StockBatch.batch_no,
                BatchRecall.product_id,
                Product.name,
                Product.sku,
                Warehouse.name,
                StockBatch.quantity,
                BatchRecall.reason,
                BatchRecall.severity,
                BatchRecall.status,
                BatchRecall.initiated_at,
                BatchRecall.resolved_at,
            )
        )

        if status:
            stmt = stmt.where(BatchRecall.status == status)
        if severity:
            stmt = stmt.where(BatchRecall.severity == severity)
        if product_id:
            stmt = stmt.where(BatchRecall.product_id == product_id)
        if search:
            q = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Product.name.ilike(q),
                    Product.sku.ilike(q),
                    StockBatch.batch_no.ilike(q),
                    BatchRecall.reason.ilike(q),
                )
            )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.session.execute(count_stmt).scalar() or 0

        offset = (page - 1) * page_size if page > 0 else 0
        stmt = stmt.order_by(desc(BatchRecall.initiated_at)).offset(offset).limit(page_size)

        rows = self.session.execute(stmt).mappings().all()
        results: list[dict[str, Any]] = [
            {
                "id": r["id"],
                "batch_id": r["batch_id"],
                "batch_no": r["batch_no"],
                "product_id": r["product_id"],
                "product_name": r["product_name"],
                "product_sku": r["product_sku"],
                "warehouse_name": r["warehouse_name"],
                "remaining_quantity": float(r["remaining_quantity"] or 0),
                "reason": r["reason"],
                "severity": r["severity"],
                "status": r["status"],
                "initiated_at": r["initiated_at"],
                "resolved_at": r["resolved_at"],
                "affected_orders_count": int(r["affected_orders_count"] or 0),
                "notified_count": int(r["notified_count"] or 0),
            }
            for r in rows
        ]

        return results, total

    def mark_affected_orders_notified(self, recall_id: str) -> tuple[int, int]:
        recall = self.session.get(BatchRecall, recall_id)
        if not recall:
            raise ValueError(f"Batch recall '{recall_id}' not found.")

        now = datetime.now(UTC)
        affected = list(
            self.session.scalars(
                select(RecallAffectedOrder).where(RecallAffectedOrder.recall_id == recall_id)
            ).all()
        )

        retailers_count = 0
        customers_count = 0

        for aff in affected:
            if aff.retailer_id:
                retailers_count += 1
            if aff.customer_id:
                customers_count += 1
            if aff.notified_at is None:
                aff.notified_at = now

        recall.status = RecallStatusEnum.NOTIFYING
        self.session.commit()
        return retailers_count, customers_count

    def resolve_recall(self, recall_id: str) -> BatchRecall:
        recall = self.session.get(BatchRecall, recall_id)
        if not recall:
            raise ValueError(f"Batch recall '{recall_id}' not found.")

        recall.status = RecallStatusEnum.RESOLVED
        recall.resolved_at = datetime.now(UTC)
        self.session.commit()
        self.session.refresh(recall)
        return recall


class InMemoryRecallRepository(RecallRepositoryInterface):
    """InMemory repository mock for fast testing of recall tracing and notification dispatch."""

    def __init__(
        self,
        recalls: list[dict[str, Any]] | None = None,
        affected_orders: list[dict[str, Any]] | None = None,
        movements: list[dict[str, Any]] | None = None,
        orders: list[dict[str, Any]] | None = None,
        retailers: list[dict[str, Any]] | None = None,
        customers: list[dict[str, Any]] | None = None,
        batches: list[dict[str, Any]] | None = None,
        products: list[dict[str, Any]] | None = None,
        warehouses: list[dict[str, Any]] | None = None,
    ):
        self.recalls = {r["id"]: dict(r) for r in (recalls or [])}
        self.affected_orders = {a["id"]: dict(a) for a in (affected_orders or [])}
        self.movements = list(movements or [])
        self.orders = {o["id"]: dict(o) for o in (orders or [])}
        self.retailers = {r["id"]: dict(r) for r in (retailers or [])}
        self.customers = {c["id"]: dict(c) for c in (customers or [])}
        self.batches = {b["id"]: dict(b) for b in (batches or [])}
        self.products = {p["id"]: dict(p) for p in (products or [])}
        self.warehouses = {w["id"]: dict(w) for w in (warehouses or [])}

    def create_recall(
        self,
        batch_id: str,
        product_id: str,
        reason: str,
        severity: RecallSeverityEnum = RecallSeverityEnum.MEDIUM,
    ) -> BatchRecall:
        r_id = str(uuid.uuid4())
        rec = {
            "id": r_id,
            "batch_id": batch_id,
            "product_id": product_id,
            "reason": reason,
            "severity": severity,
            "status": RecallStatusEnum.INITIATED,
            "initiated_at": datetime.now(UTC),
            "resolved_at": None,
        }
        self.recalls[r_id] = rec
        return BatchRecall(**rec)

    def find_affected_orders_by_batch(self, batch_id: str) -> list[dict[str, Any]]:
        # Find all OUT movements for this batch where reference_type == sales_order
        affected_so_ids: dict[str, float] = {}
        for m in self.movements:
            if (
                m.get("batch_id") == batch_id
                and m.get("type") == StockMovementTypeEnum.OUT
                and m.get("reference_type") == "sales_order"
            ):
                so_id = m.get("reference_id")
                if so_id:
                    affected_so_ids[so_id] = affected_so_ids.get(so_id, 0.0) + abs(float(m.get("quantity", 0)))

        results: list[dict[str, Any]] = []
        for so_id, qty in affected_so_ids.items():
            order = self.orders.get(so_id, {})
            b_type = order.get("buyer_type", "retailer")
            ret_id = order.get("retailer_id")
            cust_id = order.get("customer_id")

            if b_type == "retailer" and ret_id:
                ret = self.retailers.get(ret_id, {})
                buyer_name = ret.get("name", "Unknown Retailer")
                buyer_phone = ret.get("phone")
                buyer_email = ret.get("email")
                buyer_id = ret_id
            elif cust_id:
                cust = self.customers.get(cust_id, {})
                buyer_name = cust.get("name", "Walk-in Customer")
                buyer_phone = cust.get("phone")
                buyer_email = cust.get("email")
                buyer_id = cust_id
            else:
                buyer_name = "Direct Buyer"
                buyer_phone = None
                buyer_email = None
                buyer_id = None

            results.append(
                {
                    "sales_order_id": so_id,
                    "sales_order_number": so_id,
                    "buyer_type": b_type,
                    "buyer_id": buyer_id,
                    "retailer_id": ret_id,
                    "customer_id": cust_id,
                    "buyer_name": buyer_name,
                    "buyer_phone": buyer_phone,
                    "buyer_email": buyer_email,
                    "order_date": order.get("created_at"),
                    "quantity_supplied": qty,
                }
            )

        return results

    def populate_affected_orders(
        self, recall_id: str, affected_orders_data: list[dict[str, Any]]
    ) -> list[RecallAffectedOrder]:
        records: list[RecallAffectedOrder] = []
        for item in affected_orders_data:
            rec_id = str(uuid.uuid4())
            data = {
                "id": rec_id,
                "recall_id": recall_id,
                "sales_order_id": item["sales_order_id"],
                "retailer_id": item.get("retailer_id"),
                "customer_id": item.get("customer_id"),
                "notified_at": None,
            }
            self.affected_orders[rec_id] = data
            records.append(RecallAffectedOrder(**data))
        return records

    def get_recall_by_id(self, recall_id: str) -> BatchRecall | None:
        rec = self.recalls.get(recall_id)
        if not rec:
            return None

        # Build ORM model with populated attributes
        batch_dict = self.batches.get(rec["batch_id"], {})
        prod_dict = self.products.get(rec["product_id"], {})
        wh_dict = self.warehouses.get(batch_dict.get("warehouse_id", ""), {})

        batch_orm = StockBatch(**batch_dict) if batch_dict else None
        if batch_orm:
            batch_orm.warehouse = Warehouse(**wh_dict) if wh_dict else None

        prod_orm = Product(**prod_dict) if prod_dict else None

        # Gather affected orders
        aff_list: list[RecallAffectedOrder] = []
        for a in self.affected_orders.values():
            if a["recall_id"] == recall_id:
                aff_orm = RecallAffectedOrder(**a)
                if a.get("retailer_id") and a["retailer_id"] in self.retailers:
                    aff_orm.retailer = Retailer(**self.retailers[a["retailer_id"]])
                if a.get("customer_id") and a["customer_id"] in self.customers:
                    aff_orm.customer = Customer(**self.customers[a["customer_id"]])
                if a.get("sales_order_id") and a["sales_order_id"] in self.orders:
                    aff_orm.sales_order = SalesOrder(**self.orders[a["sales_order_id"]])
                aff_list.append(aff_orm)

        recall_orm = BatchRecall(**rec)
        recall_orm.batch = batch_orm
        recall_orm.product = prod_orm
        recall_orm.affected_orders = aff_list
        return recall_orm

    def get_active_recall_for_batch(self, batch_id: str) -> BatchRecall | None:
        for r in self.recalls.values():
            if r["batch_id"] == batch_id and r["status"] in [
                RecallStatusEnum.INITIATED,
                RecallStatusEnum.NOTIFYING,
            ]:
                return BatchRecall(**r)
        return None

    def get_all_active_recalled_batch_ids(self) -> set[str]:
        return {
            r["batch_id"]
            for r in self.recalls.values()
            if r["status"] in [RecallStatusEnum.INITIATED, RecallStatusEnum.NOTIFYING]
        }

    def list_recalls(
        self,
        page: int = 1,
        page_size: int = 50,
        status: str | None = None,
        severity: str | None = None,
        product_id: str | None = None,
        search: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        filtered = list(self.recalls.values())
        if status:
            filtered = [r for r in filtered if r["status"] == status]
        if severity:
            filtered = [r for r in filtered if r["severity"] == severity]
        if product_id:
            filtered = [r for r in filtered if r["product_id"] == product_id]
        if search:
            q = search.lower()
            filtered = [
                r
                for r in filtered
                if q in r.get("reason", "").lower()
                or q in self.products.get(r["product_id"], {}).get("name", "").lower()
                or q in self.batches.get(r["batch_id"], {}).get("batch_no", "").lower()
            ]

        total = len(filtered)
        offset = (page - 1) * page_size
        paged = filtered[offset : offset + page_size]

        results: list[dict[str, Any]] = []
        for r in paged:
            batch = self.batches.get(r["batch_id"], {})
            prod = self.products.get(r["product_id"], {})
            wh = self.warehouses.get(batch.get("warehouse_id", ""), {})

            affs = [a for a in self.affected_orders.values() if a["recall_id"] == r["id"]]
            notified_count = len([a for a in affs if a.get("notified_at") is not None])

            results.append(
                {
                    "id": r["id"],
                    "batch_id": r["batch_id"],
                    "batch_no": batch.get("batch_no", "—"),
                    "product_id": r["product_id"],
                    "product_name": prod.get("name", "Unknown Product"),
                    "product_sku": prod.get("sku", ""),
                    "warehouse_name": wh.get("name", "Unknown Warehouse"),
                    "remaining_quantity": float(batch.get("quantity", 0)),
                    "reason": r["reason"],
                    "severity": r["severity"],
                    "status": r["status"],
                    "initiated_at": r["initiated_at"],
                    "resolved_at": r.get("resolved_at"),
                    "affected_orders_count": len(affs),
                    "notified_count": notified_count,
                }
            )

        return results, total

    def mark_affected_orders_notified(self, recall_id: str) -> tuple[int, int]:
        rec = self.recalls.get(recall_id)
        if not rec:
            raise ValueError(f"Batch recall '{recall_id}' not found.")

        now = datetime.now(UTC)
        retailers_count = 0
        customers_count = 0

        for aff in self.affected_orders.values():
            if aff["recall_id"] == recall_id:
                if aff.get("retailer_id"):
                    retailers_count += 1
                if aff.get("customer_id"):
                    customers_count += 1
                if aff.get("notified_at") is None:
                    aff["notified_at"] = now

        rec["status"] = RecallStatusEnum.NOTIFYING
        return retailers_count, customers_count

    def resolve_recall(self, recall_id: str) -> BatchRecall:
        rec = self.recalls.get(recall_id)
        if not rec:
            raise ValueError(f"Batch recall '{recall_id}' not found.")

        rec["status"] = RecallStatusEnum.RESOLVED
        rec["resolved_at"] = datetime.now(UTC)
        return BatchRecall(**rec)
