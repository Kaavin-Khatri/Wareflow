"""SQLAlchemy and In-Memory implementations of TransferRepositoryInterface."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session, aliased

from app.models.catalog import Product
from app.models.inventory import StockMovement, StockMovementTypeEnum
from app.models.warehouse import StockBatch, Warehouse
from app.repositories.interfaces.transfer_repository import TransferRepositoryInterface


class SqlAlchemyTransferRepository(TransferRepositoryInterface):
    """Production SQLAlchemy implementation enforcing atomic inter-warehouse transfers."""

    def __init__(self, session: Session):
        self.session = session

    def execute_transfer(
        self,
        product_id: str,
        batch_id: str,
        from_warehouse_id: str,
        to_warehouse_id: str,
        quantity: float,
        notes: str | None = None,
        created_by: str | None = None,
    ) -> tuple[str, StockBatch, StockBatch, StockMovement, StockMovement]:
        qty = float(quantity)
        if qty <= 0:
            raise ValueError("Transfer quantity must be greater than zero.")

        if from_warehouse_id == to_warehouse_id:
            raise ValueError("Source and destination warehouses cannot be the same.")

        # 1. Verify warehouses exist
        from_wh = self.session.get(Warehouse, from_warehouse_id)
        if not from_wh:
            raise ValueError(f"Source warehouse '{from_warehouse_id}' not found.")

        to_wh = self.session.get(Warehouse, to_warehouse_id)
        if not to_wh:
            raise ValueError(f"Destination warehouse '{to_warehouse_id}' not found.")

        # 2. Verify source batch and available stock
        source_batch = self.session.get(StockBatch, batch_id)
        if not source_batch:
            raise ValueError(f"Source stock batch '{batch_id}' not found.")

        if source_batch.product_id != product_id:
            raise ValueError("Source batch does not match the specified product.")

        if source_batch.warehouse_id != from_warehouse_id:
            raise ValueError("Source batch is not located in the specified source warehouse.")

        if float(source_batch.quantity) < qty:
            raise ValueError(
                f"Insufficient stock in source batch. Requested {qty:.2f}, available {float(source_batch.quantity):.2f}"
            )

        transfer_id = str(uuid.uuid4())

        try:
            # 3. Decrement source batch
            source_batch.quantity = float(source_batch.quantity) - qty

            # 4. Find or create destination batch
            dest_stmt = select(StockBatch).where(
                StockBatch.product_id == product_id,
                StockBatch.warehouse_id == to_warehouse_id,
                StockBatch.batch_no == source_batch.batch_no,
            )
            if source_batch.expiry_date:
                dest_stmt = dest_stmt.where(StockBatch.expiry_date == source_batch.expiry_date)
            else:
                dest_stmt = dest_stmt.where(StockBatch.expiry_date.is_(None))

            dest_batch = self.session.execute(dest_stmt).scalar_one_or_none()

            if dest_batch:
                dest_batch.quantity = float(dest_batch.quantity) + qty
            else:
                dest_batch = StockBatch(
                    id=str(uuid.uuid4()),
                    product_id=product_id,
                    warehouse_id=to_warehouse_id,
                    batch_no=source_batch.batch_no,
                    quantity=qty,
                    expiry_date=source_batch.expiry_date,
                    received_at=datetime.now(UTC),
                )
                self.session.add(dest_batch)

            ref_id = f"{transfer_id}:{notes}" if notes else transfer_id

            # 5. Paired Outbound Movement (Source)
            out_movement = StockMovement(
                id=str(uuid.uuid4()),
                product_id=product_id,
                warehouse_id=from_warehouse_id,
                batch_id=source_batch.id,
                type=StockMovementTypeEnum.OUT,
                quantity=-qty,
                reference_type="warehouse_transfer",
                reference_id=ref_id,
                created_by=created_by,
            )

            # 6. Paired Inbound Movement (Destination)
            in_movement = StockMovement(
                id=str(uuid.uuid4()),
                product_id=product_id,
                warehouse_id=to_warehouse_id,
                batch_id=dest_batch.id,
                type=StockMovementTypeEnum.IN,
                quantity=qty,
                reference_type="warehouse_transfer",
                reference_id=ref_id,
                created_by=created_by,
            )

            self.session.add(out_movement)
            self.session.add(in_movement)
            self.session.commit()

            self.session.refresh(source_batch)
            self.session.refresh(dest_batch)
            self.session.refresh(out_movement)
            self.session.refresh(in_movement)

            return transfer_id, source_batch, dest_batch, out_movement, in_movement

        except Exception:
            self.session.rollback()
            raise

    def list_transfers(
        self,
        page: int = 1,
        page_size: int = 50,
        product_id: str | None = None,
        from_warehouse_id: str | None = None,
        to_warehouse_id: str | None = None,
        start_date: Any | None = None,
        end_date: Any | None = None,
        search: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        out_mov = aliased(StockMovement, name="out_mov")
        in_mov = aliased(StockMovement, name="in_mov")
        prod = aliased(Product, name="prod")
        from_wh = aliased(Warehouse, name="from_wh")
        to_wh = aliased(Warehouse, name="to_wh")
        src_batch = aliased(StockBatch, name="src_batch")

        stmt = (
            select(
                out_mov.id.label("out_id"),
                out_mov.product_id,
                prod.name.label("product_name"),
                prod.sku.label("product_sku"),
                out_mov.warehouse_id.label("from_warehouse_id"),
                from_wh.name.label("from_warehouse_name"),
                in_mov.warehouse_id.label("to_warehouse_id"),
                to_wh.name.label("to_warehouse_name"),
                func.coalesce(src_batch.batch_no, "—").label("batch_no"),
                func.abs(out_mov.quantity).label("quantity"),
                out_mov.reference_id,
                out_mov.created_by,
                out_mov.created_at,
            )
            .join(
                in_mov,
                (in_mov.reference_type == "warehouse_transfer")
                & (in_mov.reference_id == out_mov.reference_id)
                & (in_mov.quantity > 0),
            )
            .join(prod, prod.id == out_mov.product_id)
            .join(from_wh, from_wh.id == out_mov.warehouse_id)
            .join(to_wh, to_wh.id == in_mov.warehouse_id)
            .outerjoin(src_batch, src_batch.id == out_mov.batch_id)
            .where(
                out_mov.reference_type == "warehouse_transfer",
                out_mov.quantity < 0,
            )
        )

        if product_id:
            stmt = stmt.where(out_mov.product_id == product_id)
        if from_warehouse_id:
            stmt = stmt.where(out_mov.warehouse_id == from_warehouse_id)
        if to_warehouse_id:
            stmt = stmt.where(in_mov.warehouse_id == to_warehouse_id)
        if start_date:
            stmt = stmt.where(out_mov.created_at >= start_date)
        if end_date:
            stmt = stmt.where(out_mov.created_at <= end_date)
        if search:
            q = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    prod.name.ilike(q),
                    prod.sku.ilike(q),
                    src_batch.batch_no.ilike(q),
                    from_wh.name.ilike(q),
                    to_wh.name.ilike(q),
                )
            )

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.session.execute(count_stmt).scalar() or 0

        # Pagination
        offset = (page - 1) * page_size if page > 0 else 0
        stmt = stmt.order_by(desc(out_mov.created_at)).offset(offset).limit(page_size)

        rows = self.session.execute(stmt).mappings().all()

        results: list[dict[str, Any]] = []
        for r in rows:
            ref_id_raw = r["reference_id"] or ""
            notes = None
            trf_id = ref_id_raw
            if ":" in ref_id_raw:
                trf_id, notes = ref_id_raw.split(":", 1)

            results.append(
                {
                    "id": trf_id,
                    "product_id": r["product_id"],
                    "product_name": r["product_name"],
                    "product_sku": r["product_sku"],
                    "from_warehouse_id": r["from_warehouse_id"],
                    "from_warehouse_name": r["from_warehouse_name"],
                    "to_warehouse_id": r["to_warehouse_id"],
                    "to_warehouse_name": r["to_warehouse_name"],
                    "batch_no": r["batch_no"],
                    "quantity": float(r["quantity"]),
                    "created_by": r["created_by"],
                    "created_at": r["created_at"],
                    "notes": notes,
                }
            )

        return results, total


class InMemoryTransferRepository(TransferRepositoryInterface):
    """In-memory mock implementation of TransferRepository for unit testing."""

    def __init__(
        self,
        warehouses: list[dict[str, Any]] | None = None,
        products: list[dict[str, Any]] | None = None,
        batches: list[dict[str, Any]] | None = None,
    ):
        self.warehouses = {w["id"]: dict(w) for w in (warehouses or [])}
        self.products = {p["id"]: dict(p) for p in (products or [])}
        self.batches = {b["id"]: dict(b) for b in (batches or [])}
        self.movements: list[dict[str, Any]] = []
        self.transfers: list[dict[str, Any]] = []

    def execute_transfer(
        self,
        product_id: str,
        batch_id: str,
        from_warehouse_id: str,
        to_warehouse_id: str,
        quantity: float,
        notes: str | None = None,
        created_by: str | None = None,
    ) -> tuple[str, StockBatch, StockBatch, StockMovement, StockMovement]:
        qty = float(quantity)
        if qty <= 0:
            raise ValueError("Transfer quantity must be greater than zero.")

        if from_warehouse_id == to_warehouse_id:
            raise ValueError("Source and destination warehouses cannot be the same.")

        if from_warehouse_id not in self.warehouses:
            raise ValueError(f"Source warehouse '{from_warehouse_id}' not found.")

        if to_warehouse_id not in self.warehouses:
            raise ValueError(f"Destination warehouse '{to_warehouse_id}' not found.")

        source_batch_dict = self.batches.get(batch_id)
        if not source_batch_dict:
            raise ValueError(f"Source stock batch '{batch_id}' not found.")

        if source_batch_dict["product_id"] != product_id:
            raise ValueError("Source batch does not match the specified product.")

        if source_batch_dict["warehouse_id"] != from_warehouse_id:
            raise ValueError("Source batch is not located in the specified source warehouse.")

        if float(source_batch_dict["quantity"]) < qty:
            raise ValueError(
                f"Insufficient stock in source batch. Requested {qty:.2f}, available {float(source_batch_dict['quantity']):.2f}"
            )

        transfer_id = str(uuid.uuid4())

        # Decrement source
        source_batch_dict["quantity"] = float(source_batch_dict["quantity"]) - qty


        # Find or create destination batch
        dest_batch_dict = None
        for b in self.batches.values():
            if (
                b["product_id"] == product_id
                and b["warehouse_id"] == to_warehouse_id
                and b["batch_no"] == source_batch_dict["batch_no"]
                and b.get("expiry_date") == source_batch_dict.get("expiry_date")
            ):
                dest_batch_dict = b
                break

        if dest_batch_dict:
            dest_batch_dict["quantity"] = float(dest_batch_dict["quantity"]) + qty
        else:
            dest_id = str(uuid.uuid4())
            dest_batch_dict = {
                "id": dest_id,
                "product_id": product_id,
                "warehouse_id": to_warehouse_id,
                "batch_no": source_batch_dict["batch_no"],
                "quantity": qty,
                "expiry_date": source_batch_dict.get("expiry_date"),
                "received_at": datetime.now(UTC),
            }
            self.batches[dest_id] = dest_batch_dict

        ref_id = f"{transfer_id}:{notes}" if notes else transfer_id
        now = datetime.now(UTC)

        out_movement_dict = {
            "id": str(uuid.uuid4()),
            "product_id": product_id,
            "warehouse_id": from_warehouse_id,
            "batch_id": batch_id,
            "type": StockMovementTypeEnum.OUT,
            "quantity": -qty,
            "reference_type": "warehouse_transfer",
            "reference_id": ref_id,
            "created_by": created_by,
            "created_at": now,
        }

        in_movement_dict = {
            "id": str(uuid.uuid4()),
            "product_id": product_id,
            "warehouse_id": to_warehouse_id,
            "batch_id": dest_batch_dict["id"],
            "type": StockMovementTypeEnum.IN,
            "quantity": qty,
            "reference_type": "warehouse_transfer",
            "reference_id": ref_id,
            "created_by": created_by,
            "created_at": now,
        }

        self.movements.append(out_movement_dict)
        self.movements.append(in_movement_dict)

        # Store transfer entry
        prod = self.products.get(product_id, {})
        from_wh = self.warehouses.get(from_warehouse_id, {})
        to_wh = self.warehouses.get(to_warehouse_id, {})

        self.transfers.append(
            {
                "id": transfer_id,
                "product_id": product_id,
                "product_name": prod.get("name", "Unknown Product"),
                "product_sku": prod.get("sku", ""),
                "from_warehouse_id": from_warehouse_id,
                "from_warehouse_name": from_wh.get("name", "Unknown Warehouse"),
                "to_warehouse_id": to_warehouse_id,
                "to_warehouse_name": to_wh.get("name", "Unknown Warehouse"),
                "batch_no": source_batch_dict["batch_no"],
                "quantity": qty,
                "created_by": created_by,
                "created_at": now,
                "notes": notes,
            }
        )

        source_batch = StockBatch(**source_batch_dict)
        dest_batch = StockBatch(**dest_batch_dict)
        out_movement = StockMovement(**out_movement_dict)
        in_movement = StockMovement(**in_movement_dict)

        return transfer_id, source_batch, dest_batch, out_movement, in_movement

    def list_transfers(
        self,
        page: int = 1,
        page_size: int = 50,
        product_id: str | None = None,
        from_warehouse_id: str | None = None,
        to_warehouse_id: str | None = None,
        start_date: Any | None = None,
        end_date: Any | None = None,
        search: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        filtered = list(self.transfers)
        if product_id:
            filtered = [t for t in filtered if t["product_id"] == product_id]
        if from_warehouse_id:
            filtered = [t for t in filtered if t["from_warehouse_id"] == from_warehouse_id]
        if to_warehouse_id:
            filtered = [t for t in filtered if t["to_warehouse_id"] == to_warehouse_id]
        if start_date:
            filtered = [t for t in filtered if t["created_at"] >= start_date]
        if end_date:
            filtered = [t for t in filtered if t["created_at"] <= end_date]
        if search:
            q = search.lower()
            filtered = [
                t
                for t in filtered
                if q in t["product_name"].lower()
                or q in t["product_sku"].lower()
                or q in t["batch_no"].lower()
                or q in t["from_warehouse_name"].lower()
                or q in t["to_warehouse_name"].lower()
            ]

        total = len(filtered)
        offset = (page - 1) * page_size
        paged = filtered[offset : offset + page_size]
        return paged, total
