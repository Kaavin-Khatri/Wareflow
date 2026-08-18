"""FastAPI router for GST-compliant wholesale invoices."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query, status

from app.core.di import get_invoice_service
from app.core.security import CurrentUser, get_current_user, require_permission
from app.schemas.invoices import InvoiceListResponse, InvoiceResponse
from app.services.invoice_service import InvoiceService

router = APIRouter(tags=["invoices"])


@router.post(
    "/sales-orders/{order_id}/invoice",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate GST tax invoice for confirmed sales order",
)
def generate_invoice_for_sales_order(
    order_id: str,
    invoice_service: InvoiceService = Depends(get_invoice_service),
    current_user: CurrentUser = Depends(require_permission("orders:manage")),
) -> InvoiceResponse:
    """
    Generate or retrieve an existing GST-ready tax invoice for a sales order.

    Idempotent: Subsequent calls return the frozen invoice snapshot.
    """
    return invoice_service.generate_invoice_for_sales_order(
        sales_order_id=order_id,
        current_user=current_user,
    )


@router.get(
    "/invoices",
    response_model=InvoiceListResponse,
    summary="List wholesale invoices with optional filters",
)
def list_invoices(
    retailer_id: str | None = Query(None, description="Filter by retailer ID"),
    status: str | None = Query(None, description="Filter by payment status (unpaid, paid, etc.)"),
    start_date: datetime | None = Query(None, description="Filter invoices from date"),
    end_date: datetime | None = Query(None, description="Filter invoices up to date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    invoice_service: InvoiceService = Depends(get_invoice_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> InvoiceListResponse:
    """Fetch paginated, filterable tax invoice records."""
    return invoice_service.list_invoices(
        retailer_id=retailer_id,
        status_filter=status,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/invoices/{invoice_id}",
    response_model=InvoiceResponse,
    summary="Get invoice details by ID",
)
def get_invoice(
    invoice_id: str,
    invoice_service: InvoiceService = Depends(get_invoice_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> InvoiceResponse:
    """Fetch full invoice details including frozen line item snapshots."""
    return invoice_service.get_invoice(invoice_id=invoice_id)
