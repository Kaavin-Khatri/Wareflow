"""Supplier Portal Service for magic link access and ready-for-dispatch signaling."""

from datetime import UTC, datetime, timedelta
import logging
import secrets
from typing import Any
import uuid

from fastapi import HTTPException, status

from app.models.portal import SupplierAccessToken
from app.models.supplier import POStatusEnum, PurchaseOrder
from app.repositories.interfaces.profile_repository import ProfileRepository
from app.repositories.interfaces.purchase_order_repository import PurchaseOrderRepositoryInterface
from app.repositories.interfaces.supplier_access_token_repository import (
    SupplierAccessTokenRepositoryInterface,
)
from app.schemas.supplier_portal import (
    ReadyForDispatchResponse,
    SupplierPortalPOItemResponse,
    SupplierPortalPOResponse,
)
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class SupplierPortalService:
    """Domain service managing supplier magic-link token lifecycle and dispatch signals."""

    def __init__(
        self,
        token_repo: SupplierAccessTokenRepositoryInterface,
        po_repo: PurchaseOrderRepositoryInterface,
        profile_repo: ProfileRepository | None = None,
        notification_service: NotificationService | None = None,
        audit_service: AuditService | None = None,
    ) -> None:
        self._token_repo = token_repo
        self._po_repo = po_repo
        self._profile_repo = profile_repo
        self._notif_service = notification_service
        self._audit_service = audit_service

    def generate_access_token(
        self, supplier_id: str, purchase_order_id: str, expiry_days: int = 30
    ) -> SupplierAccessToken:
        """Create a 30-day single-purpose magic link access token for a supplier PO."""
        existing = self._token_repo.get_by_purchase_order_id(purchase_order_id)
        if existing:
            self._token_repo.delete(existing.id)

        token_str = secrets.token_urlsafe(48)
        now = datetime.now(UTC)
        token_entity = SupplierAccessToken(
            id=str(uuid.uuid4()),
            supplier_id=supplier_id,
            purchase_order_id=purchase_order_id,
            token=token_str,
            expires_at=now + timedelta(days=expiry_days),
            created_at=now,
        )
        return self._token_repo.create(token_entity)

    def _validate_token_and_get_po(self, token_str: str) -> tuple[SupplierAccessToken, PurchaseOrder]:
        """Validate token exists and has not expired, returning token and PO."""
        token_obj = self._token_repo.get_by_token(token_str)
        if not token_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid or expired magic link.",
            )

        now = datetime.now(UTC)
        exp = token_obj.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=UTC)

        if now > exp:
            self._token_repo.delete(token_obj.id)
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="This magic link has expired.",
            )

        po = self._po_repo.get_by_id(token_obj.purchase_order_id)
        if not po:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated purchase order not found.",
            )
        return token_obj, po

    def get_po_by_token(self, token_str: str) -> SupplierPortalPOResponse:
        """Retrieve read-only PO representation via magic link."""
        _, po = self._validate_token_and_get_po(token_str)
        supplier_name = po.supplier.name if po.supplier else "Unknown Supplier"

        items = [
            SupplierPortalPOItemResponse(
                id=item.id,
                product_name=item.product.name if item.product else "Unknown Product",
                product_sku=item.product.sku if item.product else "SKU-UNKNOWN",
                qty_ordered=float(item.qty_ordered),
                qty_received=float(item.qty_received),
                unit_cost=float(item.unit_cost),
                uom_name=item.uom.name if item.uom else None,
                base_uom_name=getattr(item.product, "unit", None) if item.product else None,
                line_total=round(float(item.qty_ordered) * float(item.unit_cost), 2),
            )
            for item in (po.items or [])
        ]

        return SupplierPortalPOResponse(
            po_id=po.id,
            po_number=po.po_number,
            supplier_id=po.supplier_id,
            supplier_name=supplier_name,
            status=po.status.value if hasattr(po.status, "value") else str(po.status),
            order_date=po.order_date,
            expected_date=po.expected_date,
            total_amount=float(po.total_amount),
            items=items,
        )

    def mark_ready_for_dispatch(self, token_str: str) -> ReadyForDispatchResponse:
        """Process supplier's ready-for-dispatch signal, update PO, invalidate token, and notify staff."""
        token_obj, po = self._validate_token_and_get_po(token_str)

        if po.status != POStatusEnum.ORDERED:
            if po.status == POStatusEnum.READY_FOR_DISPATCH:
                self._token_repo.delete(token_obj.id)
                return ReadyForDispatchResponse(
                    po_number=po.po_number,
                    status=po.status.value,
                    message="Purchase order is already marked ready for dispatch.",
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot mark purchase order in '{po.status.value}' status as ready for dispatch.",
            )

        self._po_repo.update_status(po.id, POStatusEnum.READY_FOR_DISPATCH)
        self._token_repo.delete(token_obj.id)

        self._log_dispatch_audit(po)
        self._notify_purchasing_staff(po)

        return ReadyForDispatchResponse(
            po_number=po.po_number,
            status=POStatusEnum.READY_FOR_DISPATCH.value,
            message="Purchase order successfully marked ready for dispatch. Warehouse staff notified.",
        )

    def _log_dispatch_audit(self, po: PurchaseOrder) -> None:
        """Record immutable audit log entry for supplier dispatch action."""
        if not self._audit_service:
            return
        supplier_name = po.supplier.name if po.supplier else "Supplier"
        self._audit_service.log_action(
            actor_id=f"supplier:{po.supplier_id}",
            action="purchase_order_marked_ready_for_dispatch",
            entity_type="purchase_order",
            entity_id=po.id,
            before_value={"status": POStatusEnum.ORDERED.value},
            after_value={"status": POStatusEnum.READY_FOR_DISPATCH.value, "supplier_name": supplier_name},
        )

    def _find_purchasing_recipients(self) -> list[tuple[str, str | None, str | None]]:
        """Identify staff recipients holding inventory/purchasing management permissions."""
        recipients: list[tuple[str, str | None, str | None]] = []
        if not self._profile_repo:
            return [("admin-system-user", "admin@wareflow.io", None)]

        try:
            profiles = self._profile_repo.list_all(limit=100)
            for p in profiles:
                if not getattr(p, "is_active", True):
                    continue
                perms = set(self._profile_repo.get_role_permissions(p.role_id))
                role_name = p.role.name if p.role else ""
                if "inventory:manage" in perms or role_name in ("Owner", "Admin", "Operations Manager"):
                    recipients.append((p.id, getattr(p, "email", None), getattr(p, "phone", None)))
        except Exception as exc:
            logger.warning("Error finding purchasing staff recipients: %s", exc)

        return recipients or [("admin-system-user", "admin@wareflow.io", None)]

    def _notify_purchasing_staff(self, po: PurchaseOrder) -> None:
        """Dispatch multi-channel alerts (In-App, Email, WhatsApp) to purchasing managers."""
        if not self._notif_service:
            return

        supplier_name = po.supplier.name if po.supplier else "Supplier"
        title = f"PO {po.po_number} Ready for Dispatch"
        body = f"Supplier '{supplier_name}' has marked Purchase Order {po.po_number} as ready for dispatch/pickup."
        meta = {
            "order_number": po.po_number,
            "po_number": po.po_number,
            "supplier_name": supplier_name,
            "summary": "Ready for pickup / dispatch",
            "link": "/admin/purchase-orders",
        }

        recipients = self._find_purchasing_recipients()
        for user_id, email, phone in recipients:
            try:
                self._notif_service.notify(
                    user_id=user_id,
                    type="goods_ready",
                    title=title,
                    body=body,
                    channels=["in_app", "email", "whatsapp"],
                    recipient_email=email,
                    recipient_phone=phone,
                    metadata=meta,
                )
            except Exception as exc:
                logger.error("Failed to notify user %s for PO dispatch: %s", user_id, exc)
