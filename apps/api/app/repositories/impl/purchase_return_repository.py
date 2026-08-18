"""Concrete implementations of PurchaseReturnRepositoryInterface."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.returns import PurchaseReturn, PurchaseReturnItem, PurchaseReturnStatusEnum
from app.repositories.interfaces.purchase_return_repository import (
    PurchaseReturnRepositoryInterface,
)


class SqlAlchemyPurchaseReturnRepository(PurchaseReturnRepositoryInterface):
    """Production SQLAlchemy implementation of PurchaseReturnRepositoryInterface."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        purchase_order_id: str,
        supplier_id: str,
        reason: str | None,
        items: list[dict],
    ) -> PurchaseReturn:
        return_id = str(uuid.uuid4())
        ret = PurchaseReturn(
            id=return_id,
            purchase_order_id=purchase_order_id,
            supplier_id=supplier_id,
            status=PurchaseReturnStatusEnum.REQUESTED,
            reason=reason,
        )
        self.session.add(ret)

        for item_data in items:
            item = PurchaseReturnItem(
                id=str(uuid.uuid4()),
                return_id=return_id,
                product_id=item_data["product_id"],
                batch_id=item_data.get("batch_id"),
                qty=float(item_data["qty"]),
                reason=item_data.get("reason"),
            )
            self.session.add(item)

        self.session.flush()
        return self.get_by_id(return_id)  # type: ignore[return-value]

    def get_by_id(self, return_id: str) -> PurchaseReturn | None:
        stmt = (
            select(PurchaseReturn)
            .options(
                joinedload(PurchaseReturn.supplier),
                joinedload(PurchaseReturn.purchase_order),
                joinedload(PurchaseReturn.items).joinedload(PurchaseReturnItem.product),
                joinedload(PurchaseReturn.items).joinedload(PurchaseReturnItem.batch),
            )
            .where(PurchaseReturn.id == return_id)
        )
        return self.session.execute(stmt).unique().scalar_one_or_none()

    def list_all(
        self,
        supplier_id: str | None = None,
        status: PurchaseReturnStatusEnum | None = None,
        purchase_order_id: str | None = None,
    ) -> list[PurchaseReturn]:
        stmt = (
            select(PurchaseReturn)
            .options(
                joinedload(PurchaseReturn.supplier),
                joinedload(PurchaseReturn.purchase_order),
                joinedload(PurchaseReturn.items).joinedload(PurchaseReturnItem.product),
                joinedload(PurchaseReturn.items).joinedload(PurchaseReturnItem.batch),
            )
            .order_by(PurchaseReturn.requested_at.desc())
        )
        if supplier_id:
            stmt = stmt.where(PurchaseReturn.supplier_id == supplier_id)
        if status:
            stmt = stmt.where(PurchaseReturn.status == status)
        if purchase_order_id:
            stmt = stmt.where(PurchaseReturn.purchase_order_id == purchase_order_id)

        return list(self.session.execute(stmt).scalars().unique().all())

    def update_status(
        self,
        return_id: str,
        status: PurchaseReturnStatusEnum,
        credit_note_ref: str | None = None,
    ) -> PurchaseReturn | None:
        ret = self.get_by_id(return_id)
        if not ret:
            return None

        ret.status = status
        if credit_note_ref is not None:
            ret.credit_note_ref = credit_note_ref.strip()

        self.session.flush()
        return ret


class InMemoryPurchaseReturnRepository(PurchaseReturnRepositoryInterface):
    """In-memory implementation of PurchaseReturnRepositoryInterface for unit testing."""

    def __init__(self, initial_returns: list[dict[str, Any]] | None = None):
        self.returns: dict[str, dict[str, Any]] = {}
        if initial_returns:
            for r in initial_returns:
                self.returns[r["id"]] = dict(r)

    def create(
        self,
        purchase_order_id: str,
        supplier_id: str,
        reason: str | None,
        items: list[dict],
    ) -> PurchaseReturn:
        return_id = str(uuid.uuid4())
        created_items = []
        for itm in items:
            created_items.append(
                {
                    "id": str(uuid.uuid4()),
                    "return_id": return_id,
                    "product_id": itm["product_id"],
                    "batch_id": itm.get("batch_id"),
                    "qty": float(itm["qty"]),
                    "reason": itm.get("reason"),
                }
            )

        data = {
            "id": return_id,
            "purchase_order_id": purchase_order_id,
            "supplier_id": supplier_id,
            "status": PurchaseReturnStatusEnum.REQUESTED,
            "reason": reason,
            "credit_note_ref": None,
            "requested_at": datetime.now(UTC),
            "items": created_items,
        }
        self.returns[return_id] = data
        return self._to_model(data)

    def get_by_id(self, return_id: str) -> PurchaseReturn | None:
        data = self.returns.get(return_id)
        if not data:
            return None
        return self._to_model(data)

    def list_all(
        self,
        supplier_id: str | None = None,
        status: PurchaseReturnStatusEnum | None = None,
        purchase_order_id: str | None = None,
    ) -> list[PurchaseReturn]:
        results = []
        for r in self.returns.values():
            if supplier_id and r["supplier_id"] != supplier_id:
                continue
            if status and r["status"] != status:
                continue
            if purchase_order_id and r["purchase_order_id"] != purchase_order_id:
                continue
            results.append(self._to_model(r))

        results.sort(key=lambda x: x.requested_at, reverse=True)
        return results

    def update_status(
        self,
        return_id: str,
        status: PurchaseReturnStatusEnum,
        credit_note_ref: str | None = None,
    ) -> PurchaseReturn | None:
        data = self.returns.get(return_id)
        if not data:
            return None

        data["status"] = status
        if credit_note_ref is not None:
            data["credit_note_ref"] = credit_note_ref.strip()

        return self._to_model(data)

    def _to_model(self, data: dict[str, Any]) -> PurchaseReturn:
        ret = PurchaseReturn(
            id=data["id"],
            purchase_order_id=data["purchase_order_id"],
            supplier_id=data["supplier_id"],
            status=data["status"],
            reason=data.get("reason"),
            credit_note_ref=data.get("credit_note_ref"),
            requested_at=data.get("requested_at", datetime.now(UTC)),
        )
        items_models = []
        for itm in data.get("items", []):
            item_model = PurchaseReturnItem(
                id=itm["id"],
                return_id=itm["return_id"],
                product_id=itm["product_id"],
                batch_id=itm.get("batch_id"),
                qty=float(itm["qty"]),
                reason=itm.get("reason"),
            )
            items_models.append(item_model)
        ret.items = items_models
        return ret
