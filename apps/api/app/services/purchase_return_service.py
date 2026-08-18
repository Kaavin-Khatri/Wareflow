import contextlib
from datetime import datetime

from fastapi import HTTPException, status

from app.models.returns import PurchaseReturn, PurchaseReturnItem, PurchaseReturnStatusEnum
from app.repositories.interfaces.product_repository import ProductRepositoryInterface
from app.repositories.interfaces.purchase_order_repository import PurchaseOrderRepositoryInterface
from app.repositories.interfaces.purchase_return_repository import (
    PurchaseReturnRepositoryInterface,
)
from app.repositories.interfaces.stock_repository import StockRepositoryInterface
from app.repositories.interfaces.supplier_repository import SupplierRepositoryInterface
from app.schemas.purchase_returns import (
    PurchaseReturnCreateRequest,
    PurchaseReturnItemResponse,
    PurchaseReturnResponse,
    PurchaseReturnStatusUpdateRequest,
)
from app.services.audit_service import AuditService


class PurchaseReturnService:
    """Domain service for outbound supplier return requests (RMA Out)."""

    def __init__(
        self,
        purchase_return_repo: PurchaseReturnRepositoryInterface,
        purchase_order_repo: PurchaseOrderRepositoryInterface,
        supplier_repo: SupplierRepositoryInterface,
        product_repo: ProductRepositoryInterface,
        stock_repo: StockRepositoryInterface,
        audit_service: AuditService | None = None,
    ):
        self.purchase_return_repo = purchase_return_repo
        self.purchase_order_repo = purchase_order_repo
        self.supplier_repo = supplier_repo
        self.product_repo = product_repo
        self.stock_repo = stock_repo
        self.audit_service = audit_service

    def _to_item_response(self, item: PurchaseReturnItem) -> PurchaseReturnItemResponse:
        prod_name = "Unknown Product"
        prod_sku = "N/A"
        if getattr(item, "product", None):
            prod_name = item.product.name
            prod_sku = item.product.sku
        elif self.product_repo:
            prod = self.product_repo.get_by_id(item.product_id)
            if prod:
                prod_name = (
                    prod.name if hasattr(prod, "name") else prod.get("name", "Unknown Product")
                )
                prod_sku = prod.sku if hasattr(prod, "sku") else prod.get("sku", "N/A")

        batch_no = "N/A"
        if getattr(item, "batch", None):
            batch_no = item.batch.batch_no
        elif item.batch_id and self.stock_repo:
            b = self.stock_repo.get_batch_by_id(item.batch_id)
            if b:
                batch_no = b.batch_no if hasattr(b, "batch_no") else b.get("batch_no", "N/A")

        return PurchaseReturnItemResponse(
            id=item.id,
            return_id=item.return_id,
            product_id=item.product_id,
            product_name=prod_name,
            product_sku=prod_sku,
            qty=float(item.qty),
            batch_id=item.batch_id,
            batch_no=batch_no,
            reason=item.reason,
        )

    def _to_response(self, ret: PurchaseReturn) -> PurchaseReturnResponse:
        supplier_name = "Unknown Supplier"
        if getattr(ret, "supplier", None):
            supplier_name = ret.supplier.name
        elif self.supplier_repo:
            sup = self.supplier_repo.get_by_id(ret.supplier_id)
            if sup:
                supplier_name = (
                    sup.name if hasattr(sup, "name") else sup.get("name", "Unknown Supplier")
                )

        po_number = "N/A"
        if getattr(ret, "purchase_order", None):
            po_number = ret.purchase_order.po_number
        elif self.purchase_order_repo:
            po = self.purchase_order_repo.get_by_id(ret.purchase_order_id)
            if po:
                po_number = po.po_number if hasattr(po, "po_number") else po.get("po_number", "N/A")

        items_resp = [self._to_item_response(itm) for itm in getattr(ret, "items", [])]
        total_qty = sum(float(i.qty) for i in items_resp)

        return PurchaseReturnResponse(
            id=ret.id,
            purchase_order_id=ret.purchase_order_id,
            po_number=po_number,
            supplier_id=ret.supplier_id,
            supplier_name=supplier_name,
            status=ret.status,
            reason=ret.reason,
            credit_note_ref=ret.credit_note_ref,
            requested_at=getattr(ret, "requested_at", None) or datetime.now(),
            items_count=len(items_resp),
            total_qty=round(total_qty, 2),
            items=items_resp,
        )

    def create_purchase_return(
        self,
        payload: PurchaseReturnCreateRequest,
        actor_id: str | None = None,
    ) -> PurchaseReturnResponse:
        """
        Create a new Purchase Return (RMA Out) request and immediately deduct stock:
        - Validates PO existence and status.
        - Validates stock batch quantities.
        - Writes StockMovement(type=return_out) rows immediately upon creation.
        """
        po = self.purchase_order_repo.get_by_id(payload.purchase_order_id)
        if not po:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Purchase order {payload.purchase_order_id} not found.",
            )

        po_status = getattr(po, "status", None)
        if str(po_status).lower() == "draft":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot return goods against a draft purchase order with no received items.",
            )

        supplier_id = getattr(po, "supplier_id", None)
        if not supplier_id and isinstance(po, dict):
            supplier_id = po.get("supplier_id")

        if not supplier_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Purchase order has no associated supplier.",
            )

        # 1. Pre-validate all items and batches before writing any stock movement
        validated_items = []
        for line in payload.items:
            if line.qty <= 0:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Return quantity for product {line.product_id} must be greater than 0.",
                )

            batch = self.stock_repo.get_batch_by_id(line.batch_id)
            if not batch:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Stock batch {line.batch_id} not found in inventory.",
                )

            batch_product_id = getattr(batch, "product_id", None) or (
                batch.get("product_id") if isinstance(batch, dict) else None
            )
            if batch_product_id != line.product_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Batch {line.batch_id} does not belong to product {line.product_id}.",
                )

            current_qty = float(
                getattr(batch, "quantity", 0.0)
                if not isinstance(batch, dict)
                else batch.get("quantity", 0.0)
            )
            if current_qty < line.qty:
                batch_no = getattr(batch, "batch_no", None) or (
                    batch.get("batch_no") if isinstance(batch, dict) else "N/A"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Cannot return {line.qty} units for batch '{batch_no}': "
                        f"only {current_qty} units available on hand."
                    ),
                )

            warehouse_id = getattr(batch, "warehouse_id", None) or (
                batch.get("warehouse_id") if isinstance(batch, dict) else None
            )

            validated_items.append(
                {
                    "product_id": line.product_id,
                    "batch_id": line.batch_id,
                    "warehouse_id": warehouse_id,
                    "qty": line.qty,
                    "reason": line.reason,
                }
            )

        # 2. Create the Purchase Return entity in repository
        created_ret = self.purchase_return_repo.create(
            purchase_order_id=payload.purchase_order_id,
            supplier_id=supplier_id,
            reason=payload.reason,
            items=validated_items,
        )

        # 3. Deduct stock immediately (stock_movements type=return_out)
        for itm in validated_items:
            self.stock_repo.record_stock_return(
                batch_id=itm["batch_id"],
                product_id=itm["product_id"],
                warehouse_id=itm["warehouse_id"],
                quantity=itm["qty"],
                reference_id=created_ret.id,
                created_by=actor_id,
            )

        # 4. Audit Log
        if self.audit_service and actor_id:
            with contextlib.suppress(Exception):
                self.audit_service.log_action(
                    actor_id=actor_id,
                    action="purchase_return_created",
                    entity_type="purchase_return",
                    entity_id=created_ret.id,
                    before_value=None,
                    after_value={
                        "purchase_order_id": payload.purchase_order_id,
                        "supplier_id": supplier_id,
                        "status": "requested",
                        "items_count": len(validated_items),
                    },
                )

        # Re-fetch with all joined data
        reloaded = self.purchase_return_repo.get_by_id(created_ret.id)
        return self._to_response(reloaded or created_ret)

    def update_return_status(
        self,
        return_id: str,
        payload: PurchaseReturnStatusUpdateRequest,
        actor_id: str | None = None,
    ) -> PurchaseReturnResponse:
        """
        Transition purchase return lifecycle:
        - Strict allowed transitions: requested -> shipped -> credited only.
        - credited requires credit_note_ref.
        """
        ret = self.purchase_return_repo.get_by_id(return_id)
        if not ret:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Purchase return {return_id} not found.",
            )

        current_status = getattr(ret, "status", None)
        target_status = payload.status

        # Validate allowed transitions: requested -> shipped -> credited
        allowed_next = {
            PurchaseReturnStatusEnum.REQUESTED: [PurchaseReturnStatusEnum.SHIPPED],
            PurchaseReturnStatusEnum.SHIPPED: [PurchaseReturnStatusEnum.CREDITED],
            PurchaseReturnStatusEnum.CREDITED: [],
        }

        if target_status not in allowed_next.get(current_status, []):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Invalid status transition from '{current_status}' to '{target_status}'. "
                    f"Allowed transitions follow 'requested' -> 'shipped' -> 'credited' only."
                ),
            )

        if target_status == PurchaseReturnStatusEnum.CREDITED and (
            not payload.credit_note_ref or not payload.credit_note_ref.strip()
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="credit_note_ref is required when marking return as credited.",
            )

        before_status = current_status
        updated = self.purchase_return_repo.update_status(
            return_id=return_id,
            status=target_status,
            credit_note_ref=payload.credit_note_ref,
        )

        if not updated:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update purchase return status.",
            )

        if self.audit_service and actor_id:
            with contextlib.suppress(Exception):
                self.audit_service.log_action(
                    actor_id=actor_id,
                    action="purchase_return_status_updated",
                    entity_type="purchase_return",
                    entity_id=return_id,
                    before_value={"status": before_status},
                    after_value={
                        "status": target_status,
                        "credit_note_ref": payload.credit_note_ref,
                    },
                )

        return self._to_response(updated)

    def get_purchase_return(self, return_id: str) -> PurchaseReturnResponse:
        """Fetch single purchase return detail by ID."""
        ret = self.purchase_return_repo.get_by_id(return_id)
        if not ret:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Purchase return {return_id} not found.",
            )
        return self._to_response(ret)

    def list_purchase_returns(
        self,
        supplier_id: str | None = None,
        status: PurchaseReturnStatusEnum | None = None,
        purchase_order_id: str | None = None,
    ) -> list[PurchaseReturnResponse]:
        """List purchase returns matching optional filter criteria."""
        returns = self.purchase_return_repo.list_all(
            supplier_id=supplier_id,
            status=status,
            purchase_order_id=purchase_order_id,
        )
        return [self._to_response(r) for r in returns]
