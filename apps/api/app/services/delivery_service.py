"""Delivery dispatch and logistics management service."""

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status

from app.models.delivery import Delivery, DeliveryStatusEnum
from app.models.retailer import BuyerTypeEnum, SalesOrder, SOStatusEnum
from app.repositories.interfaces.delivery_repository import DeliveryRepositoryInterface
from app.repositories.interfaces.sales_order_repository import (
    SalesOrderRepositoryInterface,
)
from app.schemas.deliveries import (
    DeliveryAssignRequest,
    DeliveryResponse,
    DeliveryStatusUpdateRequest,
)
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService


class DeliveryService:
    """Service orchestrating delivery dispatch, transit updates, and order sync."""

    def __init__(
        self,
        delivery_repo: DeliveryRepositoryInterface,
        sales_order_repo: SalesOrderRepositoryInterface,
        audit_service: AuditService | None = None,
        notification_service: NotificationService | None = None,
    ):
        self.delivery_repo = delivery_repo
        self.sales_order_repo = sales_order_repo
        self.audit_service = audit_service
        self.notification_service = notification_service

    def assign_delivery(
        self, sales_order_id: str, payload: DeliveryAssignRequest, current_user: Any = None
    ) -> DeliveryResponse:
        """Assign driver and vehicle to packed sales order, advancing status to shipped."""
        order = self._get_and_validate_order_for_dispatch(sales_order_id)
        delivery = self.delivery_repo.get_by_sales_order_id(sales_order_id)
        
        if delivery:
            delivery.driver_name = payload.driver_name
            delivery.vehicle_no = payload.vehicle_no
            delivery.notes = payload.notes
            delivery.status = DeliveryStatusEnum.ASSIGNED
            delivery = self.delivery_repo.update(delivery)
        else:
            delivery = Delivery(
                id=str(uuid.uuid4()),
                sales_order_id=order.id,
                driver_name=payload.driver_name,
                vehicle_no=payload.vehicle_no,
                status=DeliveryStatusEnum.ASSIGNED,
                notes=payload.notes,
                created_at=datetime.now(UTC),
            )
            delivery = self.delivery_repo.create(delivery)

        self._advance_order_on_assignment(order, current_user)
        self._audit_assignment(delivery, current_user)
        return self._to_response(delivery, order)

    def _get_and_validate_order_for_dispatch(self, sales_order_id: str) -> SalesOrder:
        order = self.sales_order_repo.get_by_id(sales_order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sales Order '{sales_order_id}' not found.",
            )
        allowed_statuses = {SOStatusEnum.PACKED, SOStatusEnum.SHIPPED}
        if order.status not in allowed_statuses:
            status_val = order.status.value if hasattr(order.status, "value") else order.status
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Cannot assign delivery for sales order with status '{status_val}' - order must be packed.",
            )
        return order

    def _advance_order_on_assignment(self, order: SalesOrder, current_user: Any = None) -> None:
        if order.status == SOStatusEnum.PACKED:
            order.status = SOStatusEnum.SHIPPED
            self.sales_order_repo.update(order)

    def update_delivery_status(
        self, delivery_id: str, payload: DeliveryStatusUpdateRequest, current_user: Any = None
    ) -> DeliveryResponse:
        """Update delivery transit status and synchronize parent sales order lifecycle."""
        delivery = self.delivery_repo.get_by_id(delivery_id)
        if not delivery:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Delivery '{delivery_id}' not found.",
            )

        if payload.status == DeliveryStatusEnum.FAILED and not (payload.notes and payload.notes.strip()):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="A failed delivery requires a notes field explaining the failure reason.",
            )

        order = self.sales_order_repo.get_by_id(delivery.sales_order_id)
        self._apply_status_transition(delivery, order, payload, current_user)
        delivery = self.delivery_repo.update(delivery)
        self._audit_status_update(delivery, payload.status, current_user)
        return self._to_response(delivery, order)

    def _apply_status_transition(
        self,
        delivery: Delivery,
        order: SalesOrder | None,
        payload: DeliveryStatusUpdateRequest,
        current_user: Any = None,
    ) -> None:
        delivery.status = payload.status
        if payload.notes:
            delivery.notes = payload.notes

        if payload.status == DeliveryStatusEnum.OUT_FOR_DELIVERY:
            delivery.dispatched_at = datetime.now(UTC)
            if order and order.status != SOStatusEnum.SHIPPED:
                order.status = SOStatusEnum.SHIPPED
                self.sales_order_repo.update(order)
        elif payload.status == DeliveryStatusEnum.DELIVERED:
            delivery.delivered_at = datetime.now(UTC)
            if order:
                order.status = SOStatusEnum.DELIVERED
                self.sales_order_repo.update(order)
        elif payload.status == DeliveryStatusEnum.FAILED:
            if self.notification_service and order:
                self._dispatch_failure_notification(order, delivery)

    def _dispatch_failure_notification(self, order: SalesOrder, delivery: Delivery) -> None:
        buyer_name = self._resolve_buyer_name(order)
        self.notification_service.send_notification(
            user_id=order.retailer_id or "staff-ops",
            type="delivery_failed",
            title=f"Delivery Failed: {order.so_number}",
            body=f"Delivery for {buyer_name} failed: {delivery.notes or 'No reason provided'}",
        )

    def get_delivery(self, delivery_id: str) -> DeliveryResponse:
        """Retrieve delivery detail by ID."""
        delivery = self.delivery_repo.get_by_id(delivery_id)
        if not delivery:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Delivery '{delivery_id}' not found.",
            )
        order = self.sales_order_repo.get_by_id(delivery.sales_order_id)
        return self._to_response(delivery, order)

    def get_delivery_by_order(self, sales_order_id: str) -> DeliveryResponse | None:
        """Retrieve delivery associated with a given sales order."""
        delivery = self.delivery_repo.get_by_sales_order_id(sales_order_id)
        if not delivery:
            return None
        order = self.sales_order_repo.get_by_id(sales_order_id)
        return self._to_response(delivery, order)

    def list_deliveries(
        self,
        status: DeliveryStatusEnum | str | None = None,
        driver_name: str | None = None,
        limit: int = 100,
        skip: int = 0,
    ) -> list[DeliveryResponse]:
        """List deliveries with optional status and driver filtering."""
        deliveries = self.delivery_repo.list_all(status=status, driver_name=driver_name, limit=limit, skip=skip)
        return [self._to_response(d) for d in deliveries]

    def _to_response(self, delivery: Delivery, order: SalesOrder | None = None) -> DeliveryResponse:
        if not order and hasattr(delivery, "sales_order") and delivery.sales_order:
            order = delivery.sales_order
        elif not order:
            order = self.sales_order_repo.get_by_id(delivery.sales_order_id)

        buyer_name = self._resolve_buyer_name(order) if order else None
        destination = self._resolve_destination(order) if order else None
        total = float(order.total_amount) if order else None

        return DeliveryResponse(
            id=delivery.id,
            sales_order_id=delivery.sales_order_id,
            so_number=order.so_number if order else None,
            buyer_name=buyer_name,
            destination_address=destination,
            driver_name=delivery.driver_name,
            vehicle_no=delivery.vehicle_no,
            status=delivery.status,
            total_amount=total,
            dispatched_at=delivery.dispatched_at,
            delivered_at=delivery.delivered_at,
            notes=delivery.notes,
            created_at=delivery.created_at,
        )

    def _resolve_buyer_name(self, order: SalesOrder | None) -> str:
        if not order:
            return "Unknown"
        if order.buyer_type == BuyerTypeEnum.RETAILER and getattr(order, "retailer", None):
            return order.retailer.name
        if order.buyer_type == BuyerTypeEnum.CUSTOMER and getattr(order, "customer", None):
            return order.customer.name
        return "Wholesale Buyer"

    def _resolve_destination(self, order: SalesOrder | None) -> str:
        if not order:
            return ""
        if order.buyer_type == BuyerTypeEnum.RETAILER and getattr(order, "retailer", None):
            return order.retailer.address or ""
        if order.buyer_type == BuyerTypeEnum.CUSTOMER and getattr(order, "customer", None):
            return order.customer.address or ""
        return ""

    def _audit_assignment(self, delivery: Delivery, current_user: Any = None) -> None:
        if self.audit_service:
            self.audit_service.log(
                action="delivery_assigned",
                entity_type="delivery",
                entity_id=delivery.id,
                before={},
                after={
                    "driver_name": delivery.driver_name,
                    "vehicle_no": delivery.vehicle_no,
                    "status": delivery.status.value,
                },
                current_user=current_user,
            )

    def _audit_status_update(
        self, delivery: Delivery, new_status: DeliveryStatusEnum, current_user: Any = None
    ) -> None:
        if self.audit_service:
            self.audit_service.log(
                action="delivery_status_updated",
                entity_type="delivery",
                entity_id=delivery.id,
                before={"status": delivery.status.value},
                after={"status": new_status.value, "notes": delivery.notes},
                current_user=current_user,
            )
