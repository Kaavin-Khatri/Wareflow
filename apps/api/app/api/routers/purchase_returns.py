"""API router for Purchase Returns (RMA Out) management."""

from fastapi import APIRouter, Depends, Query, status

from app.core.di import get_purchase_return_service
from app.core.security import CurrentUser, require_permission
from app.models.returns import PurchaseReturnStatusEnum
from app.schemas.purchase_returns import (
    PurchaseReturnCreateRequest,
    PurchaseReturnResponse,
    PurchaseReturnStatusUpdateRequest,
)
from app.services.purchase_return_service import PurchaseReturnService

router = APIRouter(prefix="/purchase-returns", tags=["purchase-returns"])


@router.get(
    "",
    response_model=list[PurchaseReturnResponse],
    summary="List purchase returns with optional supplier, status, and PO filters",
)
def list_purchase_returns(
    supplier_id: str | None = Query(None, description="Filter by supplier ID"),
    status_filter: PurchaseReturnStatusEnum | None = Query(
        None, alias="status", description="Filter by return status"
    ),
    purchase_order_id: str | None = Query(None, description="Filter by original purchase order ID"),
    service: PurchaseReturnService = Depends(get_purchase_return_service),
    current_user: CurrentUser = Depends(require_permission("inventory:view")),
) -> list[PurchaseReturnResponse]:
    """Retrieve all purchase returns matching optional filter criteria."""
    return service.list_purchase_returns(
        supplier_id=supplier_id,
        status=status_filter,
        purchase_order_id=purchase_order_id,
    )


@router.post(
    "",
    response_model=PurchaseReturnResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a purchase return request and immediately deduct stock",
)
def create_purchase_return(
    payload: PurchaseReturnCreateRequest,
    service: PurchaseReturnService = Depends(get_purchase_return_service),
    current_user: CurrentUser = Depends(require_permission("inventory:manage")),
) -> PurchaseReturnResponse:
    """
    Create a new supplier RMA return request.
    Stock is deducted from inventory and logged in stock_movements(type=return_out) immediately.
    """
    return service.create_purchase_return(payload=payload, actor_id=current_user.id)


@router.get(
    "/{id}",
    response_model=PurchaseReturnResponse,
    summary="Get single purchase return detail by ID",
)
def get_purchase_return(
    id: str,
    service: PurchaseReturnService = Depends(get_purchase_return_service),
    current_user: CurrentUser = Depends(require_permission("inventory:view")),
) -> PurchaseReturnResponse:
    """Retrieve purchase return details and item lines by ID."""
    return service.get_purchase_return(return_id=id)


@router.patch(
    "/{id}/status",
    response_model=PurchaseReturnResponse,
    summary="Update purchase return status (requested -> shipped -> credited)",
)
def update_purchase_return_status(
    id: str,
    payload: PurchaseReturnStatusUpdateRequest,
    service: PurchaseReturnService = Depends(get_purchase_return_service),
    current_user: CurrentUser = Depends(require_permission("inventory:manage")),
) -> PurchaseReturnResponse:
    """
    Transition return lifecycle.
    - requested -> shipped -> credited only.
    - credited requires credit_note_ref.
    """
    return service.update_return_status(
        return_id=id,
        payload=payload,
        actor_id=current_user.id,
    )
