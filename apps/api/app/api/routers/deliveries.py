"""Deliveries & Logistics Status API router."""

from fastapi import APIRouter, Depends, Query, status

from app.core.di import get_delivery_service
from app.core.security import CurrentUser, get_current_user, require_permission
from app.schemas.deliveries import (
    DeliveryResponse,
    DeliveryStatusUpdateRequest,
)
from app.services.delivery_service import DeliveryService

router = APIRouter(prefix="/deliveries", tags=["Deliveries & Logistics"])


@router.get(
    "",
    response_model=list[DeliveryResponse],
    status_code=status.HTTP_200_OK,
    summary="List delivery dispatches",
)
def list_deliveries(
    status_filter: str | None = Query(None, alias="status", description="Filter by delivery status"),
    driver_name: str | None = Query(None, description="Filter by assigned driver name"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: CurrentUser = Depends(get_current_user),
    delivery_service: DeliveryService = Depends(get_delivery_service),
) -> list[DeliveryResponse]:
    """Retrieve all delivery records with optional status or driver filter."""
    return delivery_service.list_deliveries(
        status=status_filter,
        driver_name=driver_name,
        limit=limit,
        skip=skip,
    )


@router.get(
    "/{id}",
    response_model=DeliveryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get delivery by ID",
)
def get_delivery(
    id: str,
    current_user: CurrentUser = Depends(get_current_user),
    delivery_service: DeliveryService = Depends(get_delivery_service),
) -> DeliveryResponse:
    """Retrieve single delivery record with sales order details."""
    return delivery_service.get_delivery(delivery_id=id)


@router.patch(
    "/{id}/status",
    response_model=DeliveryResponse,
    status_code=status.HTTP_200_OK,
    summary="Update delivery transit status",
)
def update_delivery_status(
    id: str,
    payload: DeliveryStatusUpdateRequest,
    current_user: CurrentUser = Depends(require_permission("inventory:manage")),
    delivery_service: DeliveryService = Depends(get_delivery_service),
) -> DeliveryResponse:
    """
    Update delivery status across dispatch lifecycle:
    - out_for_delivery: sets dispatched_at, confirms order is shipped
    - delivered: sets delivered_at, automatically flips sales order status to DELIVERED
    - failed: requires notes explaining cause, keeps order in shipped status without false completion
    """
    return delivery_service.update_delivery_status(
        delivery_id=id, payload=payload, current_user=current_user
    )
