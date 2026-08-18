import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.catalog import Product
from app.models.inventory import StockMovement, StockMovementTypeEnum
from app.models.warehouse import StockBatch, Warehouse
from app.repositories.interfaces.stock_repository import StockRepositoryInterface


class SqlAlchemyStockRepository(StockRepositoryInterface):
    """Production SQLAlchemy implementation of StockRepositoryInterface."""

    def __init__(self, session: Session):
        self.session = session

    def get_on_hand(self, product_id: str, warehouse_id: str | None = None) -> float:
        stmt = select(func.coalesce(func.sum(StockBatch.quantity), 0)).where(
            StockBatch.product_id == product_id
        )
        if warehouse_id:
            stmt = stmt.where(StockBatch.warehouse_id == warehouse_id)
        result = self.session.execute(stmt).scalar()
        return float(result or 0.0)

    def get_batches_by_product(
        self, product_id: str, warehouse_id: str | None = None
    ) -> list[StockBatch]:
        stmt = (
            select(StockBatch)
            .options(
                joinedload(StockBatch.warehouse),
                joinedload(StockBatch.product).joinedload(Product.base_uom),
            )
            .where(StockBatch.product_id == product_id)
        )
        if warehouse_id:
            stmt = stmt.where(StockBatch.warehouse_id == warehouse_id)
        stmt = stmt.order_by(
            StockBatch.expiry_date.asc().nullslast(),
            StockBatch.received_at.asc(),
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_batches_expiring_soon(
        self, days: int = 30, warehouse_id: str | None = None
    ) -> list[StockBatch]:
        target_date = date.today() + timedelta(days=days)
        stmt = (
            select(StockBatch)
            .options(
                joinedload(StockBatch.warehouse),
                joinedload(StockBatch.product).joinedload(Product.base_uom),
            )
            .where(
                StockBatch.quantity > 0,
                StockBatch.expiry_date.is_not(None),
                StockBatch.expiry_date <= target_date,
            )
        )
        if warehouse_id:
            stmt = stmt.where(StockBatch.warehouse_id == warehouse_id)
        stmt = stmt.order_by(StockBatch.expiry_date.asc())
        return list(self.session.execute(stmt).scalars().all())

    def get_all_warehouses(self, active_only: bool = True) -> list[Warehouse]:
        stmt = select(Warehouse)
        if active_only:
            stmt = stmt.where(Warehouse.is_active.is_(True))
        stmt = stmt.order_by(Warehouse.name.asc())
        return list(self.session.execute(stmt).scalars().all())

    def get_warehouse_by_id(self, warehouse_id: str) -> Warehouse | None:
        return self.session.get(Warehouse, warehouse_id)

    def get_product_with_base_uom(self, product_id: str) -> Product | None:
        stmt = (
            select(Product)
            .options(joinedload(Product.base_uom), joinedload(Product.category))
            .where(Product.id == product_id)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_stock_overview_data(
        self,
        warehouse_id: str | None = None,
        category_id: str | None = None,
        search: str | None = None,
    ) -> list[dict[str, Any]]:
        # 1. Fetch active products
        prod_stmt = (
            select(Product)
            .options(joinedload(Product.base_uom), joinedload(Product.category))
            .where(Product.is_active.is_(True))
        )
        if category_id:
            prod_stmt = prod_stmt.where(Product.category_id == category_id)
        if search:
            s = f"%{search.strip()}%"
            prod_stmt = prod_stmt.where(
                or_(
                    Product.name.ilike(s),
                    Product.sku.ilike(s),
                    Product.barcode.ilike(s),
                )
            )
        prod_stmt = prod_stmt.order_by(Product.name.asc())
        products = list(self.session.execute(prod_stmt).scalars().all())

        if not products:
            return []

        prod_ids = [p.id for p in products]

        # 2. Fetch batches for these products
        batch_stmt = (
            select(StockBatch)
            .options(joinedload(StockBatch.warehouse))
            .where(StockBatch.product_id.in_(prod_ids))
        )
        if warehouse_id:
            batch_stmt = batch_stmt.where(StockBatch.warehouse_id == warehouse_id)
        batches = list(self.session.execute(batch_stmt).scalars().all())

        # 3. Aggregate batches per product and warehouse
        batches_by_prod: dict[str, list[StockBatch]] = {}
        for b in batches:
            batches_by_prod.setdefault(b.product_id, []).append(b)

        overview_rows: list[dict[str, Any]] = []
        for p in products:
            prod_batches = batches_by_prod.get(p.id, [])
            total_on_hand = sum(float(b.quantity) for b in prod_batches)

            # Per-warehouse breakdown
            wh_map: dict[str, dict[str, Any]] = {}
            for b in prod_batches:
                wh_id = b.warehouse_id
                wh_name = b.warehouse.name if b.warehouse else "Unknown Warehouse"
                if wh_id not in wh_map:
                    wh_map[wh_id] = {
                        "warehouse_id": wh_id,
                        "warehouse_name": wh_name,
                        "on_hand": 0.0,
                        "batch_count": 0,
                    }
                wh_map[wh_id]["on_hand"] = round(wh_map[wh_id]["on_hand"] + float(b.quantity), 2)
                wh_map[wh_id]["batch_count"] += 1

            overview_rows.append(
                {
                    "product": p,
                    "total_on_hand": round(total_on_hand, 2),
                    "warehouses": list(wh_map.values()),
                    "batches": prod_batches,
                }
            )

        return overview_rows

    def record_stock_receipt(
        self,
        product_id: str,
        warehouse_id: str,
        batch_no: str,
        quantity: float,
        expiry_date: Any | None = None,
        reference_id: str | None = None,
        created_by: str | None = None,
    ) -> tuple[StockBatch, StockMovement]:
        clean_batch_no = batch_no.strip().upper()
        # 1. Find existing batch with matching identity
        stmt = select(StockBatch).where(
            StockBatch.product_id == product_id,
            StockBatch.warehouse_id == warehouse_id,
            StockBatch.batch_no == clean_batch_no,
        )
        batch = self.session.execute(stmt).scalar_one_or_none()

        if batch:
            batch.quantity = round(float(batch.quantity) + float(quantity), 2)
            if expiry_date and not batch.expiry_date:
                batch.expiry_date = expiry_date
        else:
            batch = StockBatch(
                id=str(uuid.uuid4()),
                product_id=product_id,
                warehouse_id=warehouse_id,
                batch_no=clean_batch_no,
                quantity=round(float(quantity), 2),
                expiry_date=expiry_date,
            )
            self.session.add(batch)

        self.session.flush()

        # 2. Insert immutable StockMovement(type=in) ledger row
        movement = StockMovement(
            id=str(uuid.uuid4()),
            product_id=product_id,
            warehouse_id=warehouse_id,
            batch_id=batch.id,
            type=StockMovementTypeEnum.IN,
            quantity=round(float(quantity), 2),
            reference_type="purchase_order",
            reference_id=reference_id,
            created_by=created_by,
        )
        self.session.add(movement)
        self.session.flush()

        return batch, movement

    def get_batch_by_id(self, batch_id: str) -> StockBatch | None:
        stmt = (
            select(StockBatch)
            .options(
                joinedload(StockBatch.warehouse),
                joinedload(StockBatch.product).joinedload(Product.base_uom),
            )
            .where(StockBatch.id == batch_id)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def record_stock_return(
        self,
        batch_id: str,
        product_id: str,
        warehouse_id: str,
        quantity: float,
        reference_id: str | None = None,
        created_by: str | None = None,
    ) -> tuple[StockBatch, StockMovement]:
        stmt = select(StockBatch).where(StockBatch.id == batch_id)
        batch = self.session.execute(stmt).scalar_one_or_none()
        if not batch:
            raise ValueError(f"Stock batch {batch_id} not found.")

        current_qty = float(batch.quantity)
        if current_qty < float(quantity):
            raise ValueError(
                f"Cannot return {quantity} units: batch {batch.batch_no} only has {current_qty} on hand."
            )

        batch.quantity = round(current_qty - float(quantity), 2)
        self.session.flush()

        movement = StockMovement(
            id=str(uuid.uuid4()),
            product_id=product_id or batch.product_id,
            warehouse_id=warehouse_id or batch.warehouse_id,
            batch_id=batch.id,
            type=StockMovementTypeEnum.RETURN_OUT,
            quantity=round(float(quantity), 2),
            reference_type="purchase_return",
            reference_id=reference_id,
            created_by=created_by,
        )
        self.session.add(movement)
        self.session.flush()

        return batch, movement

    def deduct_stock_fifo(
        self,
        product_id: str,
        quantity: float,
        warehouse_id: str | None = None,
        reference_type: str = "sales_order",
        reference_id: str | None = None,
        created_by: str | None = None,
    ) -> list[tuple[StockBatch, float, StockMovement]]:
        target_qty = round(float(quantity), 2)
        if target_qty <= 0:
            return []

        batches = self.get_batches_by_product(product_id, warehouse_id)
        active_batches = [b for b in batches if float(b.quantity) > 0]
        total_available = round(sum(float(b.quantity) for b in active_batches), 2)

        if total_available < target_qty:
            shortfall = round(target_qty - total_available, 2)
            prod = self.get_product_with_base_uom(product_id)
            prod_name = prod.name if prod else product_id
            sku_info = f" (SKU: {prod.sku})" if prod and prod.sku else ""
            raise ValueError(
                f"Insufficient stock for product '{prod_name}'{sku_info}: required {target_qty}, available {total_available}, shortfall {shortfall}."
            )

        deductions: list[tuple[StockBatch, float, StockMovement]] = []
        remaining_qty = target_qty

        for batch in active_batches:
            if remaining_qty <= 0:
                break
            batch_available = float(batch.quantity)
            deduct_amount = min(batch_available, remaining_qty)
            batch.quantity = round(batch_available - deduct_amount, 2)
            self.session.flush()

            movement = StockMovement(
                id=str(uuid.uuid4()),
                product_id=product_id,
                warehouse_id=batch.warehouse_id,
                batch_id=batch.id,
                type=StockMovementTypeEnum.OUT,
                quantity=round(deduct_amount, 2),
                reference_type=reference_type,
                reference_id=reference_id,
                created_by=created_by,
            )
            self.session.add(movement)
            self.session.flush()

            deductions.append((batch, deduct_amount, movement))
            remaining_qty = round(remaining_qty - deduct_amount, 2)

        return deductions

    def restore_sales_order_stock(
        self,
        sales_order_id: str,
        reason: str = "Order Cancelled",
        created_by: str | None = None,
    ) -> list[StockMovement]:
        stmt = select(StockMovement).where(
            StockMovement.reference_type == "sales_order",
            StockMovement.reference_id == sales_order_id,
            StockMovement.type == StockMovementTypeEnum.OUT,
        )
        out_movements = list(self.session.execute(stmt).scalars().all())
        compensating_movements: list[StockMovement] = []

        for out_mov in out_movements:
            if out_mov.batch_id:
                batch = self.session.get(StockBatch, out_mov.batch_id)
                if batch:
                    batch.quantity = round(float(batch.quantity) + float(out_mov.quantity), 2)
                    self.session.flush()

            adj_movement = StockMovement(
                id=str(uuid.uuid4()),
                product_id=out_mov.product_id,
                warehouse_id=out_mov.warehouse_id,
                batch_id=out_mov.batch_id,
                type=StockMovementTypeEnum.ADJUSTMENT,
                quantity=round(float(out_mov.quantity), 2),
                reference_type="sales_order_cancellation",
                reference_id=sales_order_id,
                created_by=created_by,
            )
            self.session.add(adj_movement)
            self.session.flush()
            compensating_movements.append(adj_movement)

        return compensating_movements


class InMemoryStockRepository(StockRepositoryInterface):
    """In-Memory implementation of StockRepositoryInterface for isolated unit tests."""

    def __init__(
        self,
        warehouses: list[dict[str, Any]] | None = None,
        products: list[dict[str, Any]] | None = None,
        batches: list[dict[str, Any]] | None = None,
    ):
        self.warehouses: dict[str, dict[str, Any]] = {}
        self.products: dict[str, dict[str, Any]] = {}
        self.batches: dict[str, dict[str, Any]] = {}
        self.movements: list[dict[str, Any]] = []

        if warehouses:
            for w in warehouses:
                self.warehouses[w["id"]] = dict(w)
        if products:
            for p in products:
                self.products[p["id"]] = dict(p)
        if batches:
            for b in batches:
                self.batches[b["id"]] = dict(b)

    def _to_batch_model(self, data: dict[str, Any]) -> StockBatch:
        batch = StockBatch(
            id=data["id"],
            product_id=data["product_id"],
            warehouse_id=data["warehouse_id"],
            batch_no=data["batch_no"],
            quantity=float(data["quantity"]),
            expiry_date=data.get("expiry_date"),
        )
        batch.received_at = data.get("received_at", datetime.now(UTC))
        if data["warehouse_id"] in self.warehouses:
            wh_data = self.warehouses[data["warehouse_id"]]
            batch.warehouse = Warehouse(
                id=wh_data["id"],
                name=wh_data["name"],
                location=wh_data.get("location"),
                is_active=wh_data.get("is_active", True),
            )
        if data["product_id"] in self.products:
            prod_data = self.products[data["product_id"]]
            batch.product = Product(
                id=prod_data["id"],
                sku=prod_data["sku"],
                name=prod_data["name"],
                reorder_point=prod_data.get("reorder_point", 10),
                reorder_qty=prod_data.get("reorder_qty", 50),
                cost_price=prod_data.get("cost_price", 0.0),
                wholesale_price=prod_data.get("wholesale_price", 0.0),
                is_active=prod_data.get("is_active", True),
            )
        return batch

    def get_on_hand(self, product_id: str, warehouse_id: str | None = None) -> float:
        total = 0.0
        for b in self.batches.values():
            if b["product_id"] == product_id and (
                warehouse_id is None or b["warehouse_id"] == warehouse_id
            ):
                total += float(b["quantity"])
        return round(total, 2)

    def get_batches_by_product(
        self, product_id: str, warehouse_id: str | None = None
    ) -> list[StockBatch]:
        res: list[StockBatch] = []
        for b in self.batches.values():
            if b["product_id"] == product_id and (
                warehouse_id is None or b["warehouse_id"] == warehouse_id
            ):
                res.append(self._to_batch_model(b))
        res.sort(
            key=lambda x: (
                x.expiry_date if x.expiry_date else date.max,
                x.received_at or datetime.min,
            )
        )
        return res

    def get_batches_expiring_soon(
        self, days: int = 30, warehouse_id: str | None = None
    ) -> list[StockBatch]:
        target_date = date.today() + timedelta(days=days)
        res: list[StockBatch] = []
        for b in self.batches.values():
            if (
                float(b["quantity"]) > 0
                and b.get("expiry_date") is not None
                and b["expiry_date"] <= target_date
                and (warehouse_id is None or b["warehouse_id"] == warehouse_id)
            ):
                res.append(self._to_batch_model(b))
        res.sort(key=lambda x: x.expiry_date or date.max)
        return res

    def get_all_warehouses(self, active_only: bool = True) -> list[Warehouse]:
        res: list[Warehouse] = []
        for w in self.warehouses.values():
            if not active_only or w.get("is_active", True):
                res.append(
                    Warehouse(
                        id=w["id"],
                        name=w["name"],
                        location=w.get("location"),
                        is_active=w.get("is_active", True),
                    )
                )
        res.sort(key=lambda x: x.name)
        return res

    def get_warehouse_by_id(self, warehouse_id: str) -> Warehouse | None:
        if warehouse_id in self.warehouses:
            w = self.warehouses[warehouse_id]
            return Warehouse(
                id=w["id"],
                name=w["name"],
                location=w.get("location"),
                is_active=w.get("is_active", True),
            )
        return None

    def get_product_with_base_uom(self, product_id: str) -> Product | None:
        if product_id in self.products:
            p = self.products[product_id]
            return Product(
                id=p["id"],
                sku=p["sku"],
                name=p["name"],
                reorder_point=p.get("reorder_point", 10),
                reorder_qty=p.get("reorder_qty", 50),
                cost_price=p.get("cost_price", 0.0),
                wholesale_price=p.get("wholesale_price", 0.0),
                is_active=p.get("is_active", True),
            )
        return None

    def get_stock_overview_data(
        self,
        warehouse_id: str | None = None,
        category_id: str | None = None,
        search: str | None = None,
    ) -> list[dict[str, Any]]:
        overview_rows: list[dict[str, Any]] = []
        for p in self.products.values():
            if not p.get("is_active", True):
                continue
            if category_id and p.get("category_id") != category_id:
                continue
            if search:
                s = search.lower()
                if s not in p["name"].lower() and s not in p["sku"].lower():
                    continue

            prod_model = Product(
                id=p["id"],
                sku=p["sku"],
                name=p["name"],
                reorder_point=p.get("reorder_point", 10),
                reorder_qty=p.get("reorder_qty", 50),
                cost_price=p.get("cost_price", 0.0),
                wholesale_price=p.get("wholesale_price", 0.0),
                is_active=p.get("is_active", True),
            )

            prod_batches = [
                self._to_batch_model(b)
                for b in self.batches.values()
                if b["product_id"] == p["id"]
                and (warehouse_id is None or b["warehouse_id"] == warehouse_id)
            ]

            total_on_hand = sum(float(b.quantity) for b in prod_batches)
            wh_map: dict[str, dict[str, Any]] = {}
            for b in prod_batches:
                wh_id = b.warehouse_id
                wh_name = b.warehouse.name if b.warehouse else "Warehouse"
                if wh_id not in wh_map:
                    wh_map[wh_id] = {
                        "warehouse_id": wh_id,
                        "warehouse_name": wh_name,
                        "on_hand": 0.0,
                        "batch_count": 0,
                    }
                wh_map[wh_id]["on_hand"] = round(wh_map[wh_id]["on_hand"] + float(b.quantity), 2)
                wh_map[wh_id]["batch_count"] += 1

            overview_rows.append(
                {
                    "product": prod_model,
                    "total_on_hand": round(total_on_hand, 2),
                    "warehouses": list(wh_map.values()),
                    "batches": prod_batches,
                }
            )

        return overview_rows

    def record_stock_receipt(
        self,
        product_id: str,
        warehouse_id: str,
        batch_no: str,
        quantity: float,
        expiry_date: Any | None = None,
        reference_id: str | None = None,
        created_by: str | None = None,
    ) -> tuple[StockBatch, StockMovement]:
        clean_batch_no = batch_no.strip().upper()
        matching_batch_id: str | None = None

        for bid, b in self.batches.items():
            if (
                b["product_id"] == product_id
                and b["warehouse_id"] == warehouse_id
                and b["batch_no"] == clean_batch_no
            ):
                matching_batch_id = bid
                break

        if matching_batch_id:
            batch_data = self.batches[matching_batch_id]
            batch_data["quantity"] = round(float(batch_data["quantity"]) + float(quantity), 2)
            if expiry_date and not batch_data.get("expiry_date"):
                batch_data["expiry_date"] = expiry_date
        else:
            matching_batch_id = str(uuid.uuid4())
            batch_data = {
                "id": matching_batch_id,
                "product_id": product_id,
                "warehouse_id": warehouse_id,
                "batch_no": clean_batch_no,
                "quantity": round(float(quantity), 2),
                "expiry_date": expiry_date,
                "received_at": datetime.now(UTC),
            }
            self.batches[matching_batch_id] = batch_data

        batch_model = self._to_batch_model(batch_data)

        movement = StockMovement(
            id=str(uuid.uuid4()),
            product_id=product_id,
            warehouse_id=warehouse_id,
            batch_id=batch_model.id,
            type=StockMovementTypeEnum.IN,
            quantity=round(float(quantity), 2),
            reference_type="purchase_order",
            reference_id=reference_id,
            created_by=created_by,
        )
        return batch_model, movement

    def get_batch_by_id(self, batch_id: str) -> StockBatch | None:
        data = self.batches.get(batch_id)
        if not data:
            return None
        return self._to_batch_model(data)

    def record_stock_return(
        self,
        batch_id: str,
        product_id: str,
        warehouse_id: str,
        quantity: float,
        reference_id: str | None = None,
        created_by: str | None = None,
    ) -> tuple[StockBatch, StockMovement]:
        data = self.batches.get(batch_id)
        if not data:
            raise ValueError(f"Stock batch {batch_id} not found.")

        current_qty = float(data["quantity"])
        if current_qty < float(quantity):
            raise ValueError(
                f"Cannot return {quantity} units: batch {data.get('batch_no')} only has {current_qty} on hand."
            )

        data["quantity"] = round(current_qty - float(quantity), 2)
        batch_model = self._to_batch_model(data)

        movement = StockMovement(
            id=str(uuid.uuid4()),
            product_id=product_id or data["product_id"],
            warehouse_id=warehouse_id or data["warehouse_id"],
            batch_id=batch_model.id,
            type=StockMovementTypeEnum.RETURN_OUT,
            quantity=round(float(quantity), 2),
            reference_type="purchase_return",
            reference_id=reference_id,
            created_by=created_by,
        )
        self.movements.append(
            {
                "id": movement.id,
                "product_id": movement.product_id,
                "warehouse_id": movement.warehouse_id,
                "batch_id": movement.batch_id,
                "type": movement.type,
                "quantity": movement.quantity,
                "reference_type": movement.reference_type,
                "reference_id": movement.reference_id,
                "created_by": movement.created_by,
            }
        )
        return batch_model, movement

    def deduct_stock_fifo(
        self,
        product_id: str,
        quantity: float,
        warehouse_id: str | None = None,
        reference_type: str = "sales_order",
        reference_id: str | None = None,
        created_by: str | None = None,
    ) -> list[tuple[StockBatch, float, StockMovement]]:
        target_qty = round(float(quantity), 2)
        if target_qty <= 0:
            return []

        batches = self.get_batches_by_product(product_id, warehouse_id)
        active_batches = [b for b in batches if float(b.quantity) > 0]
        total_available = round(sum(float(b.quantity) for b in active_batches), 2)

        if total_available < target_qty:
            shortfall = round(target_qty - total_available, 2)
            prod = self.get_product_with_base_uom(product_id)
            prod_name = prod.name if prod else product_id
            sku_info = f" (SKU: {prod.sku})" if prod and prod.sku else ""
            raise ValueError(
                f"Insufficient stock for product '{prod_name}'{sku_info}: required {target_qty}, available {total_available}, shortfall {shortfall}."
            )

        deductions: list[tuple[StockBatch, float, StockMovement]] = []
        remaining_qty = target_qty

        for batch in active_batches:
            if remaining_qty <= 0:
                break
            batch_available = float(batch.quantity)
            deduct_amount = min(batch_available, remaining_qty)

            # Update in-memory batch dictionary
            if batch.id in self.batches:
                self.batches[batch.id]["quantity"] = round(batch_available - deduct_amount, 2)
            batch.quantity = round(batch_available - deduct_amount, 2)

            movement = StockMovement(
                id=str(uuid.uuid4()),
                product_id=product_id,
                warehouse_id=batch.warehouse_id,
                batch_id=batch.id,
                type=StockMovementTypeEnum.OUT,
                quantity=round(deduct_amount, 2),
                reference_type=reference_type,
                reference_id=reference_id,
                created_by=created_by,
            )
            self.movements.append(
                {
                    "id": movement.id,
                    "product_id": movement.product_id,
                    "warehouse_id": movement.warehouse_id,
                    "batch_id": movement.batch_id,
                    "type": movement.type,
                    "quantity": movement.quantity,
                    "reference_type": movement.reference_type,
                    "reference_id": movement.reference_id,
                    "created_by": movement.created_by,
                }
            )

            deductions.append((batch, deduct_amount, movement))
            remaining_qty = round(remaining_qty - deduct_amount, 2)

        return deductions

    def restore_sales_order_stock(
        self,
        sales_order_id: str,
        reason: str = "Order Cancelled",
        created_by: str | None = None,
    ) -> list[StockMovement]:
        out_movements = [
            m
            for m in self.movements
            if m.get("reference_type") == "sales_order"
            and m.get("reference_id") == sales_order_id
            and m.get("type") == StockMovementTypeEnum.OUT
        ]
        compensating_movements: list[StockMovement] = []

        for out_mov in out_movements:
            batch_id = out_mov.get("batch_id")
            if batch_id and batch_id in self.batches:
                curr_b_qty = float(self.batches[batch_id]["quantity"])
                self.batches[batch_id]["quantity"] = round(
                    curr_b_qty + float(out_mov["quantity"]), 2
                )

            adj_movement = StockMovement(
                id=str(uuid.uuid4()),
                product_id=out_mov["product_id"],
                warehouse_id=out_mov["warehouse_id"],
                batch_id=batch_id,
                type=StockMovementTypeEnum.ADJUSTMENT,
                quantity=round(float(out_mov["quantity"]), 2),
                reference_type="sales_order_cancellation",
                reference_id=sales_order_id,
                created_by=created_by,
            )
            self.movements.append(
                {
                    "id": adj_movement.id,
                    "product_id": adj_movement.product_id,
                    "warehouse_id": adj_movement.warehouse_id,
                    "batch_id": adj_movement.batch_id,
                    "type": adj_movement.type,
                    "quantity": adj_movement.quantity,
                    "reference_type": adj_movement.reference_type,
                    "reference_id": adj_movement.reference_id,
                    "created_by": adj_movement.created_by,
                }
            )
            compensating_movements.append(adj_movement)

        return compensating_movements
