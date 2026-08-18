"""Transfer domain service orchestrating atomic inter-warehouse movements (Step 9.2)."""

import math
from typing import Any

from fastapi import HTTPException, status

from app.repositories.interfaces.audit_repository import AuditRepository
from app.repositories.interfaces.transfer_repository import TransferRepositoryInterface
from app.schemas.stock_transfers import (
    StockTransferCreateRequest,
    StockTransferListItemResponse,
    StockTransferListResponse,
    StockTransferResponse,
)


class TransferService:
    """Service handling multi-warehouse stock relocations with atomic paired movements."""

    def __init__(
        self,
        transfer_repo: TransferRepositoryInterface,
        audit_repo: AuditRepository | None = None,
    ):
        self.transfer_repo = transfer_repo
        self.audit_repo = audit_repo

    def execute_transfer(
        self, payload: StockTransferCreateRequest, current_user: Any
    ) -> StockTransferResponse:
        """
        Executes an atomic inter-warehouse transfer:
        - Validates quantities and distinct source/destination facilities
        - Performs paired OUT at source and IN at destination within a single transaction
        - Rejects transfer if source stock is insufficient (422)
        - Logs audit trail
        """
        if payload.quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transfer quantity must be greater than zero.",
            )

        if payload.from_warehouse_id == payload.to_warehouse_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Source and destination warehouses cannot be the same.",
            )

        actor = getattr(current_user, "email", None) or getattr(current_user, "id", None) or "system"

        try:
            transfer_id, src_batch, dest_batch, out_mov, in_mov = self.transfer_repo.execute_transfer(
                product_id=payload.product_id,
                batch_id=payload.batch_id,
                from_warehouse_id=payload.from_warehouse_id,
                to_warehouse_id=payload.to_warehouse_id,
                quantity=payload.quantity,
                notes=payload.notes,
                created_by=actor,
            )
        except ValueError as e:
            err_msg = str(e)
            if "not found" in err_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=err_msg,
                ) from e
            if "insufficient" in err_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=err_msg,
                ) from e
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=err_msg,
            ) from e

        # Audit logging
        if self.audit_repo:
            actor_id = getattr(current_user, "id", None)
            self.audit_repo.create_log(
                actor_id=actor_id,
                action="stock_transferred",
                entity_type="stock_transfer",
                entity_id=transfer_id,
                before_value={
                    "source_batch_id": payload.batch_id,
                    "from_warehouse_id": payload.from_warehouse_id,
                },
                after_value={
                    "destination_batch_id": dest_batch.id,
                    "to_warehouse_id": payload.to_warehouse_id,
                    "quantity": payload.quantity,
                    "notes": payload.notes,
                },
            )

        return StockTransferResponse(
            transfer_id=transfer_id,
            product_id=payload.product_id,
            from_warehouse_id=payload.from_warehouse_id,
            to_warehouse_id=payload.to_warehouse_id,
            source_batch_id=src_batch.id,
            destination_batch_id=dest_batch.id,
            quantity=payload.quantity,
            out_movement_id=out_mov.id,
            in_movement_id=in_mov.id,
            created_by=actor,
            created_at=out_mov.created_at,
            notes=payload.notes,
        )

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
    ) -> StockTransferListResponse:
        """Fetch paginated historical inter-warehouse transfer records."""
        raw_items, total = self.transfer_repo.list_transfers(
            page=page,
            page_size=page_size,
            product_id=product_id,
            from_warehouse_id=from_warehouse_id,
            to_warehouse_id=to_warehouse_id,
            start_date=start_date,
            end_date=end_date,
            search=search,
        )

        formatted_items = [
            StockTransferListItemResponse(
                id=item["id"],
                product_id=item["product_id"],
                product_name=item["product_name"],
                product_sku=item["product_sku"],
                from_warehouse_id=item["from_warehouse_id"],
                from_warehouse_name=item["from_warehouse_name"],
                to_warehouse_id=item["to_warehouse_id"],
                to_warehouse_name=item["to_warehouse_name"],
                batch_no=item["batch_no"],
                quantity=item["quantity"],
                created_by=item.get("created_by"),
                created_at=item["created_at"],
                notes=item.get("notes"),
            )
            for item in raw_items
        ]

        pages = max(1, math.ceil(total / page_size)) if page_size > 0 else 1
        return StockTransferListResponse(
            items=formatted_items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )
