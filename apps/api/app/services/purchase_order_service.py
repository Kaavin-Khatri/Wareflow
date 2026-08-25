import contextlib
from datetime import datetime
from typing import Any

from fastapi import HTTPException, status

from app.models.supplier import POStatusEnum, PurchaseOrder, PurchaseOrderItem
from app.repositories.interfaces.product_repository import ProductRepositoryInterface
from app.repositories.interfaces.purchase_order_repository import PurchaseOrderRepositoryInterface
from app.repositories.interfaces.supplier_access_token_repository import (
    SupplierAccessTokenRepositoryInterface,
)
from app.repositories.interfaces.supplier_repository import SupplierRepositoryInterface
from app.schemas.purchase_orders import (
    POCreateRequest,
    POItemResponse,
    POReceiveRequest,
    POUpdateRequest,
    PurchaseOrderResponse,
)
from app.services.audit_service import AuditService
from app.services.stock_service import StockService


def _is_active(entity: Any) -> bool:
    if isinstance(entity, dict):
        return entity.get("is_active", True)
    return getattr(entity, "is_active", True)


def _get_name(entity: Any, default: str = "Unknown") -> str:
    if isinstance(entity, dict):
        return entity.get("name", default)
    return getattr(entity, "name", default)


def _get_base_uom_id(product: Any) -> str | None:
    if isinstance(product, dict):
        return product.get("base_uom_id")
    return getattr(product, "base_uom_id", None)


class PurchaseOrderService:
    """Domain service managing Purchase Orders and authoritative goods receiving."""

    def __init__(
        self,
        po_repo: PurchaseOrderRepositoryInterface,
        supplier_repo: SupplierRepositoryInterface,
        product_repo: ProductRepositoryInterface,
        stock_service: StockService,
        audit_service: AuditService | None = None,
        supplier_portal_service: Any | None = None,
        token_repo: SupplierAccessTokenRepositoryInterface | None = None,
    ) -> None:
        self.po_repo = po_repo
        self.supplier_repo = supplier_repo
        self.product_repo = product_repo
        self.stock_service = stock_service
        self.audit_service = audit_service
        self.supplier_portal_service = supplier_portal_service
        self.token_repo = token_repo

    def _to_item_response(self, item: PurchaseOrderItem) -> POItemResponse:
        """Transform PurchaseOrderItem ORM model into POItemResponse schema."""
        product_name = item.product.name if item.product else "Unknown Product"
        product_sku = item.product.sku if item.product else "SKU-UNKNOWN"
        uom_name = item.uom.name if item.uom else None
        base_uom_name = (
            item.product.base_uom.name
            if item.product and getattr(item.product, "base_uom", None)
            else (getattr(item.product, "unit", None) if item.product else "Piece")
        )
        line_total = round(float(item.qty_ordered) * float(item.unit_cost), 2)

        return POItemResponse(
            id=item.id,
            po_id=item.po_id,
            product_id=item.product_id,
            product_name=product_name,
            product_sku=product_sku,
            qty_ordered=float(item.qty_ordered),
            qty_received=float(item.qty_received),
            unit_cost=float(item.unit_cost),
            uom_id=item.uom_id,
            uom_name=uom_name,
            base_uom_name=base_uom_name,
            line_total=line_total,
        )

    def _to_response(self, po: PurchaseOrder) -> PurchaseOrderResponse:
        """Transform PurchaseOrder ORM model into PurchaseOrderResponse schema."""
        supplier_name = po.supplier.name if (po.supplier and hasattr(po.supplier, "name")) else None
        if not supplier_name and getattr(po, "supplier_id", None) and self.supplier_repo:
            sup = self.supplier_repo.get_by_id(po.supplier_id)
            if sup:
                supplier_name = _get_name(sup, "Unknown Supplier")
        if not supplier_name:
            supplier_name = "Unknown Supplier"
        items_resp = [self._to_item_response(item) for item in (po.items or [])]
        magic_token = None
        if self.token_repo:
            token_obj = self.token_repo.get_by_purchase_order_id(po.id)
            magic_token = token_obj.token if token_obj else None

        return PurchaseOrderResponse(
            id=po.id,
            po_number=po.po_number,
            supplier_id=po.supplier_id,
            supplier_name=supplier_name,
            status=po.status,
            order_date=getattr(po, "order_date", None) or datetime.now(),
            expected_date=po.expected_date,
            total_amount=float(po.total_amount),
            items_count=len(items_resp),
            items=items_resp,
            magic_link_token=magic_token,
            created_at=getattr(po, "created_at", None) or datetime.now(),
        )

    def list_purchase_orders(
        self,
        supplier_id: str | None = None,
        status_filter: str | None = None,
        search: str | None = None,
    ) -> list[PurchaseOrderResponse]:
        """List purchase orders matching query filters."""
        pos = self.po_repo.list_purchase_orders(
            supplier_id=supplier_id,
            status=status_filter,
            search=search,
        )
        return [self._to_response(po) for po in pos]

    def get_purchase_order(self, po_id: str) -> PurchaseOrderResponse:
        """Get purchase order by ID or raise 404."""
        po = self.po_repo.get_by_id(po_id)
        if not po:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Purchase order '{po_id}' not found.",
            )
        return self._to_response(po)

    def create_draft_po(
        self, payload: POCreateRequest, actor_id: str | None = None
    ) -> PurchaseOrderResponse:
        """Create a new draft Purchase Order with line items."""
        supplier = self.supplier_repo.get_by_id(payload.supplier_id)
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Supplier '{payload.supplier_id}' not found.",
            )

        if not _is_active(supplier):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Supplier '{_get_name(supplier)}' is inactive. Cannot raise purchase orders against inactive vendors.",
            )

        if not payload.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Purchase order must contain at least one line item.",
            )

        items_data = []
        for idx, item in enumerate(payload.items):
            product = self.product_repo.get_by_id(item.product_id)
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product '{item.product_id}' on line {idx + 1} not found.",
                )
            if not _is_active(product):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product '{_get_name(product)}' is inactive and cannot be ordered.",
                )

            items_data.append(
                {
                    "product_id": item.product_id,
                    "qty_ordered": item.qty_ordered,
                    "qty_received": 0.0,
                    "unit_cost": item.unit_cost,
                    "uom_id": item.uom_id or _get_base_uom_id(product),
                }
            )

        po_data = {
            "supplier_id": payload.supplier_id,
            "expected_date": payload.expected_date,
            "status": POStatusEnum.DRAFT,
        }

        created_po = self.po_repo.create_purchase_order(po_data=po_data, items_data=items_data)

        if self.audit_service and actor_id:
            self.audit_service.log_action(
                actor_id=actor_id,
                action="purchase_order_created",
                entity_type="purchase_order",
                entity_id=created_po.id,
                before_value=None,
                after_value={
                    "po_number": created_po.po_number,
                    "supplier_id": created_po.supplier_id,
                    "total_amount": float(created_po.total_amount),
                    "items_count": len(items_data),
                },
            )

        return self._to_response(created_po)

    def update_draft_po(
        self, po_id: str, payload: POUpdateRequest, actor_id: str | None = None
    ) -> PurchaseOrderResponse:
        """Edit supplier, dates, or line items on a draft Purchase Order."""
        po = self.po_repo.get_by_id(po_id)
        if not po:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Purchase order '{po_id}' not found.",
            )

        if po.status != POStatusEnum.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot edit purchase order '{po.po_number}' in '{po.status.value}' status. Only draft purchase orders can be modified.",
            )

        po_data: dict = {}
        if payload.supplier_id is not None:
            supplier = self.supplier_repo.get_by_id(payload.supplier_id)
            if not supplier:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Supplier '{payload.supplier_id}' not found.",
                )
            if not _is_active(supplier):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Supplier '{_get_name(supplier)}' is inactive.",
                )
            po_data["supplier_id"] = payload.supplier_id

        if payload.expected_date is not None:
            po_data["expected_date"] = payload.expected_date

        items_data = None
        if payload.items is not None:
            if not payload.items:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Purchase order must contain at least one line item.",
                )
            items_data = []
            for idx, item in enumerate(payload.items):
                product = self.product_repo.get_by_id(item.product_id)
                if not product:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Product '{item.product_id}' on line {idx + 1} not found.",
                    )
                if not _is_active(product):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Product '{_get_name(product)}' is inactive and cannot be ordered.",
                    )
                items_data.append(
                    {
                        "id": item.id,
                        "product_id": item.product_id,
                        "qty_ordered": item.qty_ordered,
                        "qty_received": 0.0,
                        "unit_cost": item.unit_cost,
                        "uom_id": item.uom_id or _get_base_uom_id(product),
                    }
                )

        updated = self.po_repo.update_purchase_order(
            po_id=po_id, po_data=po_data, items_data=items_data
        )

        if self.audit_service and actor_id and updated:
            self.audit_service.log_action(
                actor_id=actor_id,
                action="purchase_order_updated",
                entity_type="purchase_order",
                entity_id=updated.id,
                before_value={"total_amount": float(po.total_amount)},
                after_value={"total_amount": float(updated.total_amount)},
            )

        return self._to_response(updated or po)

    def transition_to_ordered(
        self, po_id: str, actor_id: str | None = None
    ) -> PurchaseOrderResponse:
        """Transition a draft Purchase Order to ordered status."""
        po = self.po_repo.get_by_id(po_id)
        if not po:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Purchase order '{po_id}' not found.",
            )

        if po.status != POStatusEnum.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Purchase order '{po.po_number}' is already in '{po.status.value}' status.",
            )

        if not po.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot place order for an empty purchase order.",
            )

        updated = self.po_repo.update_status(po_id, POStatusEnum.ORDERED)

        if self.supplier_portal_service and updated:
            with contextlib.suppress(Exception):
                self.supplier_portal_service.generate_access_token(
                    supplier_id=updated.supplier_id,
                    purchase_order_id=updated.id,
                )

        if self.audit_service and actor_id and updated:
            self.audit_service.log_action(
                actor_id=actor_id,
                action="purchase_order_ordered",
                entity_type="purchase_order",
                entity_id=updated.id,
                before_value={"status": POStatusEnum.DRAFT.value},
                after_value={"status": POStatusEnum.ORDERED.value},
            )

        return self._to_response(updated or po)

    def receive_goods(
        self, po_id: str, payload: POReceiveRequest, actor_id: str | None = None
    ) -> PurchaseOrderResponse:
        """
        Receive goods for line items on an active Purchase Order:
        - Increases inventory on-hand in base UoM
        - Inserts an immutable StockMovement(type=in) record per line
        - Updates line item received quantities
        - Auto-derives PO status (partially_received vs received)
        """
        po = self.po_repo.get_by_id(po_id)
        if not po:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Purchase order '{po_id}' not found.",
            )

        if po.status in (POStatusEnum.DRAFT, POStatusEnum.CANCELLED):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot receive goods for purchase order '{po.po_number}' in '{po.status.value}' status. Order must be placed first.",
            )

        if not payload.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No items specified for goods receiving.",
            )

        items_map: dict[str, PurchaseOrderItem] = {item.id: item for item in (po.items or [])}

        for r_item in payload.items:
            po_item = items_map.get(r_item.po_item_id)
            if not po_item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Purchase order line item '{r_item.po_item_id}' not found on order '{po.po_number}'.",
                )

            if r_item.qty_received <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Received quantity must be greater than zero.",
                )

            remaining = round(float(po_item.qty_ordered) - float(po_item.qty_received), 2)
            if r_item.qty_received > remaining:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot receive {r_item.qty_received} units for line item '{po_item.product.name if po_item.product else r_item.po_item_id}'. Only {remaining} units remain pending.",
                )

            # 1. Authoritative inbound stock ledger write & batch upsert (converts to base UoM inside)
            uom_to_use = r_item.uom_id or po_item.uom_id
            self.stock_service.receive_stock(
                product_id=po_item.product_id,
                warehouse_id=r_item.warehouse_id,
                batch_no=r_item.batch_no,
                quantity=r_item.qty_received,
                uom_id=uom_to_use,
                expiry_date=r_item.expiry_date,
                reference_id=po.id,
                actor_id=actor_id,
            )

            # 2. Update line item received counter
            self.po_repo.update_item_received_qty(po_item.id, r_item.qty_received)

        # 3. Reload fresh PO state to compute derived status
        fresh_po = self.po_repo.get_by_id(po_id)
        if not fresh_po:
            return self._to_response(po)

        all_received = True
        any_received = False

        for item in fresh_po.items:
            ordered = float(item.qty_ordered)
            rec = float(item.qty_received)
            if rec > 0:
                any_received = True
            if rec < ordered:
                all_received = False

        new_status = (
            POStatusEnum.RECEIVED
            if all_received
            else (POStatusEnum.PARTIALLY_RECEIVED if any_received else fresh_po.status)
        )

        if new_status != fresh_po.status:
            fresh_po = self.po_repo.update_status(po_id, new_status) or fresh_po

        if self.audit_service and actor_id:
            self.audit_service.log_action(
                actor_id=actor_id,
                action="purchase_order_goods_received",
                entity_type="purchase_order",
                entity_id=po_id,
                before_value={"status": po.status.value},
                after_value={
                    "status": fresh_po.status.value,
                    "received_lines_count": len(payload.items),
                },
            )

        return self._to_response(fresh_po)
