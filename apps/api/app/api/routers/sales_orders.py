"""Sales Orders API router."""

from fastapi import APIRouter, Depends, Query, Response, status

from app.core.di import get_delivery_service, get_export_service, get_sales_order_service
from app.core.security import CurrentUser, get_current_user, require_permission
from app.schemas.deliveries import DeliveryAssignRequest, DeliveryResponse
from app.schemas.sales_orders import (
    SalesOrderCreateRequest,
    SalesOrderResponse,
    SalesOrderStatusUpdateRequest,
)
from app.services.delivery_service import DeliveryService
from app.services.export_service import ExportService
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


@router.post(
    "/{id}/delivery",
    response_model=DeliveryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Assign driver and vehicle delivery to packed sales order",
)
def assign_order_delivery(
    id: str,
    payload: DeliveryAssignRequest,
    current_user: CurrentUser = Depends(require_permission("inventory:manage")),
    delivery_service: DeliveryService = Depends(get_delivery_service),
) -> DeliveryResponse:
    """Assign a driver and vehicle to a packed sales order, advancing order status to shipped."""
    return delivery_service.assign_delivery(sales_order_id=id, payload=payload, current_user=current_user)


@router.get(
    "/{id}/delivery",
    response_model=DeliveryResponse | None,
    status_code=status.HTTP_200_OK,
    summary="Get delivery details for a sales order",
)
def get_order_delivery(
    id: str,
    current_user: CurrentUser = Depends(get_current_user),
    delivery_service: DeliveryService = Depends(get_delivery_service),
) -> DeliveryResponse | None:
    """Retrieve the delivery status and dispatch information for a sales order."""
    return delivery_service.get_delivery_by_order(sales_order_id=id)


@router.get(
    "/{id}/packing-slip.pdf",
    status_code=status.HTTP_200_OK,
    summary="Generate customer-facing Packing Slip PDF",
)
def get_packing_slip_pdf(
    id: str,
    current_user: CurrentUser = Depends(get_current_user),
    export_service: ExportService = Depends(get_export_service),
) -> Response:
    """
    Generate and stream print-ready customer-facing Packing Slip PDF.
    Contains distributor legal header, ship-to address, quantities shipped, and zero prices.
    """
    pdf_bytes = export_service.generate_packing_slip(sales_order_id=id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="packing-slip-{id}.pdf"'},
    )


@router.get(
    "/{id}/pick-list.pdf",
    status_code=status.HTTP_200_OK,
    summary="Generate staff-facing Warehouse Pick List PDF",
)
def get_pick_list_pdf(
    id: str,
    current_user: CurrentUser = Depends(get_current_user),
    export_service: ExportService = Depends(get_export_service),
) -> Response:
    """
    Generate and stream staff-facing Warehouse Pick List PDF.
    Contains large print checklist format, warehouse location grouping, and zero pricing info.
    """
    pdf_bytes = export_service.generate_pick_list(sales_order_id=id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="pick-list-{id}.pdf"'},
    )


@router.get(
    "/{id}/pdf",
    status_code=status.HTTP_200_OK,
    summary="Download sales order confirmation PDF",
)
def download_sales_order_pdf(
    id: str,
    current_user: CurrentUser = Depends(get_current_user),
    export_service: ExportService = Depends(get_export_service),
) -> Response:
    """Generate and download print-ready Sales Order Confirmation PDF document."""
    pdf_bytes = export_service.generate_sales_order_pdf(sales_order_id=id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="SO_{id}.pdf"'},
    )


