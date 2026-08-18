"""Sales Orders API router."""

from fastapi import APIRouter, Depends, Query, status

from app.core.di import get_sales_order_service
from app.core.security import CurrentUser, get_current_user, require_permission
from app.schemas.sales_orders import (
    SalesOrderCreateRequest,
    SalesOrderResponse,
    SalesOrderStatusUpdateRequest,
)
from app.services.sales_order_service import SalesOrderService

router = APIRouter(prefix="/sales-orders", tags=["Sales Orders"])


@router.get(
    "",
    response_model=list[SalesOrderResponse],
    status_code=status.HTTP_200_OK,
    summary="List sales orders",
)
def list_sales_orders(
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    retailer_id: str | None = Query(None, description="Filter by retailer ID"),
    buyer_type: str | None = Query(
        None, description="Filter by buyer type ('retailer' or 'customer')"
    ),
    search: str | None = Query(None, description="Search by SO number or retailer name"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: CurrentUser = Depends(get_current_user),
    service: SalesOrderService = Depends(get_sales_order_service),
) -> list[SalesOrderResponse]:
    """Retrieve list of sales orders with optional status, retailer, search, and pagination."""
    items, _ = service.list_orders(
        status=status_filter,
        retailer_id=retailer_id,
        buyer_type=buyer_type,
        search=search,
        skip=skip,
        limit=limit,
    )
    return items


@router.post(
    "",
    response_model=SalesOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create sales order",
)
def create_sales_order(
    payload: SalesOrderCreateRequest,
    current_user: CurrentUser = Depends(require_permission("inventory:manage")),
    service: SalesOrderService = Depends(get_sales_order_service),
) -> SalesOrderResponse:
    """Create a new draft sales order with line items and tier pricing."""
    return service.create_order(payload=payload, current_user=current_user)


@router.get(
    "/{id}",
    response_model=SalesOrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Get sales order by ID",
)
def get_sales_order(
    id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: SalesOrderService = Depends(get_sales_order_service),
) -> SalesOrderResponse:
    """Retrieve a single sales order record with full line items and retailer details."""
    return service.get_order(order_id=id)


@router.post(
    "/{id}/confirm",
    response_model=SalesOrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm sales order",
)
def confirm_sales_order(
    id: str,
    current_user: CurrentUser = Depends(require_permission("inventory:manage")),
    service: SalesOrderService = Depends(get_sales_order_service),
) -> SalesOrderResponse:
    """
    Confirm a draft sales order:
    1. Evaluates credit gate (rejects if credit limit exceeded, with zero stock deduction)
    2. Deducts required quantities FIFO-by-expiry across stock batches
    3. Increments retailer credit balance and marks order confirmed
    """
    return service.confirm_order(order_id=id, current_user=current_user)


@router.patch(
    "/{id}/status",
    response_model=SalesOrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Update sales order status",
)
def update_sales_order_status(
    id: str,
    payload: SalesOrderStatusUpdateRequest,
    current_user: CurrentUser = Depends(require_permission("inventory:manage")),
    service: SalesOrderService = Depends(get_sales_order_service),
) -> SalesOrderResponse:
    """
    Transition sales order status through fulfillment flow (draft -> confirmed -> packed -> shipped -> delivered).
    Cancelling a confirmed order automatically restores deducted stock batches via compensating adjustment movements.
    """
    return service.update_status(order_id=id, payload=payload, current_user=current_user)
