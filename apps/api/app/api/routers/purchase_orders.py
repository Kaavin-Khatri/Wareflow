"""Purchase Orders and Goods Receiving router."""

from fastapi import APIRouter, Depends, Query, Response, status

from app.core.di import get_export_service, get_purchase_order_service
from app.core.security import CurrentUser, get_current_user, require_permission
from app.schemas.purchase_orders import (
    POCreateRequest,
    POReceiveRequest,
    POUpdateRequest,
    PurchaseOrderResponse,
)
from app.services.export_service import ExportService
from app.services.purchase_order_service import PurchaseOrderService

router = APIRouter(prefix="/purchase-orders", tags=["Purchase Orders"])


@router.get(
    "",
    response_model=list[PurchaseOrderResponse],
    status_code=status.HTTP_200_OK,
    summary="List purchase orders",
)
def list_purchase_orders(
    supplier_id: str | None = Query(None, description="Filter by supplier ID"),
    status_filter: str | None = Query(
        None, alias="status", description="Filter by PO status (draft, ordered, etc.)"
    ),
    search: str | None = Query(None, description="Search by PO number or supplier name"),
    current_user: CurrentUser = Depends(get_current_user),
    service: PurchaseOrderService = Depends(get_purchase_order_service),
) -> list[PurchaseOrderResponse]:
    """Retrieve list of purchase orders with optional status/supplier/search filters."""
    return service.list_purchase_orders(
        supplier_id=supplier_id,
        status_filter=status_filter,
        search=search,
    )


@router.post(
    "",
    response_model=PurchaseOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create draft purchase order",
)
def create_purchase_order(
    payload: POCreateRequest,
    current_user: CurrentUser = Depends(require_permission("inventory:manage")),
    service: PurchaseOrderService = Depends(get_purchase_order_service),
) -> PurchaseOrderResponse:
    """Create a new draft Purchase Order with line items."""
    return service.create_draft_po(payload=payload, actor_id=current_user.id)


@router.get(
    "/{id}",
    response_model=PurchaseOrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Get purchase order by ID",
)
def get_purchase_order(
    id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: PurchaseOrderService = Depends(get_purchase_order_service),
) -> PurchaseOrderResponse:
    """Retrieve detailed Purchase Order record with all line items."""
    return service.get_purchase_order(po_id=id)


@router.patch(
    "/{id}",
    response_model=PurchaseOrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Update draft purchase order",
)
def update_purchase_order(
    id: str,
    payload: POUpdateRequest,
    current_user: CurrentUser = Depends(require_permission("inventory:manage")),
    service: PurchaseOrderService = Depends(get_purchase_order_service),
) -> PurchaseOrderResponse:
    """Modify supplier, delivery date, or line items for a draft purchase order."""
    return service.update_draft_po(po_id=id, payload=payload, actor_id=current_user.id)


@router.post(
    "/{id}/order",
    response_model=PurchaseOrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Place purchase order with supplier",
)
def transition_to_ordered(
    id: str,
    current_user: CurrentUser = Depends(require_permission("inventory:manage")),
    service: PurchaseOrderService = Depends(get_purchase_order_service),
) -> PurchaseOrderResponse:
    """Transition a draft Purchase Order into ordered status."""
    return service.transition_to_ordered(po_id=id, actor_id=current_user.id)


@router.post(
    "/{id}/receive",
    response_model=PurchaseOrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Receive goods against purchase order",
)
def receive_goods(
    id: str,
    payload: POReceiveRequest,
    current_user: CurrentUser = Depends(require_permission("inventory:manage")),
    service: PurchaseOrderService = Depends(get_purchase_order_service),
) -> PurchaseOrderResponse:
    """
    Authoritative single-door goods receiving pipeline:
    - Increments inventory in base UoM
    - Creates immutable StockMovement(type=in) ledger entries
    - Updates line item received counters
    - Auto-derives partially_received or received status
    """
    return service.receive_goods(po_id=id, payload=payload, actor_id=current_user.id)


@router.get(
    "/{id}/pdf",
    status_code=status.HTTP_200_OK,
    summary="Download purchase order PDF",
)
def download_purchase_order_pdf(
    id: str,
    current_user: CurrentUser = Depends(get_current_user),
    export_service: ExportService = Depends(get_export_service),
) -> Response:
    """Generate and download print-ready Purchase Order PDF document."""
    pdf_bytes = export_service.generate_purchase_order_pdf(purchase_order_id=id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=PO_{id}.pdf"},
    )
