"""FastAPI router for Retailer Sales Returns (RMA In)."""

from fastapi import APIRouter, Depends, Query, status

from app.core.di import get_sales_return_service
from app.core.security import CurrentUser, get_current_user, require_permission
from app.models.returns import SalesReturnStatusEnum
from app.schemas.sales_returns import (
    SalesReturnCreateRequest,
    SalesReturnResponse,
    SalesReturnStatusUpdateRequest,
)
from app.services.sales_return_service import SalesReturnService

router = APIRouter(prefix="/sales-returns", tags=["Sales Returns"])


@router.get(
    "",
    response_model=list[SalesReturnResponse],
    summary="List sales returns (RMA In)",
    dependencies=[Depends(require_permission("orders:view"))],
)
def list_sales_returns(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(100, ge=1, le=500, description="Page limit"),
    retailer_id: str | None = Query(None, description="Filter by retailer ID"),
    sales_order_id: str | None = Query(None, description="Filter by sales order ID"),
    status: SalesReturnStatusEnum | None = Query(None, description="Filter by status"),
    search: str | None = Query(None, description="Search query (ID, reason, retailer)"),
    service: SalesReturnService = Depends(get_sales_return_service),
) -> list[SalesReturnResponse]:
    """Retrieve filtered list of Sales Returns."""
    return service.list_returns(
        skip=skip,
        limit=limit,
        retailer_id=retailer_id,
        sales_order_id=sales_order_id,
        status_filter=status,
        search=search,
    )


@router.post(
    "",
    response_model=SalesReturnResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Request a sales return (RMA In)",
    dependencies=[Depends(require_permission("orders:create"))],
)
def create_sales_return(
    payload: SalesReturnCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: SalesReturnService = Depends(get_sales_return_service),
) -> SalesReturnResponse:
    """Initiate an inbound retailer sales return request."""
    return service.create_return(payload=payload, current_user=current_user)


@router.get(
    "/{return_id}",
    response_model=SalesReturnResponse,
    summary="Get sales return details",
    dependencies=[Depends(require_permission("orders:view"))],
)
def get_sales_return(
    return_id: str,
    service: SalesReturnService = Depends(get_sales_return_service),
) -> SalesReturnResponse:
    """Retrieve detailed record of a Sales Return."""
    return service.get_return(return_id=return_id)


@router.patch(
    "/{return_id}/approve",
    response_model=SalesReturnResponse,
    summary="Approve sales return and restock resellable items",
    dependencies=[Depends(require_permission("inventory:manage"))],
)
def approve_sales_return(
    return_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: SalesReturnService = Depends(get_sales_return_service),
) -> SalesReturnResponse:
    """
    Approve an RMA return and apply condition-based restocking:
    - Resellable items replenish on-hand stock batches with RETURN_IN movements.
    - Damaged items are recorded without entering sellable stock batches.
    """
    return service.approve_return(return_id=return_id, current_user=current_user)


@router.patch(
    "/{return_id}/reject",
    response_model=SalesReturnResponse,
    summary="Reject sales return",
    dependencies=[Depends(require_permission("orders:create"))],
)
def reject_sales_return(
    return_id: str,
    payload: SalesReturnStatusUpdateRequest | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    service: SalesReturnService = Depends(get_sales_return_service),
) -> SalesReturnResponse:
    """Reject an RMA return request without inventory restocking."""
    reason = payload.rejection_reason if payload else None
    return service.reject_return(return_id=return_id, reason=reason, current_user=current_user)
