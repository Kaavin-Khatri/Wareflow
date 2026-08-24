from datetime import datetime

from fastapi import APIRouter, Depends, Query, Response, status

from app.core.di import (
    get_einvoice_service,
    get_export_service,
    get_invoice_service,
    get_payment_service,
)
from app.core.security import CurrentUser, get_current_user, require_permission
from app.schemas.billing import (
    EInvoiceConfigResponse,
    EInvoiceGenerateResponse,
    EWayBillGenerateRequest,
    EWayBillResponse,
    OverdueDetectionResponse,
    PaymentCreateRequest,
    PaymentResponse,
)
from app.schemas.invoices import InvoiceListResponse, InvoiceResponse
from app.services.einvoice_service import EinvoiceService
from app.services.export_service import ExportService
from app.services.invoice_service import InvoiceService
from app.services.payment_service import PaymentService

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
    "/invoices/einvoice/config",
    response_model=EInvoiceConfigResponse,
    summary="Get E-Invoice and E-Way Bill statutory configuration status",
)
def get_einvoice_config(
    einvoice_service: EinvoiceService = Depends(get_einvoice_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> EInvoiceConfigResponse:
    """Retrieve current E-Invoice and E-Way bill configuration status and turnover guidelines."""
    return einvoice_service.get_config()


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


@router.post(
    "/invoices/{invoice_id}/payments",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record payment against an invoice",
)
def record_payment(
    invoice_id: str,
    payload: PaymentCreateRequest,
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: CurrentUser = Depends(require_permission("orders:manage")),
) -> PaymentResponse:
    """
    Record payment against an invoice.

    Validates amount does not exceed outstanding balance, transitions invoice status,
    and decreases the retailer's credit_balance.
    """
    return payment_service.record_payment(
        invoice_id=invoice_id,
        payload=payload,
        current_user=current_user,
    )


@router.get(
    "/invoices/{invoice_id}/payments",
    response_model=list[PaymentResponse],
    summary="List all payments recorded for an invoice",
)
def list_payments_for_invoice(
    invoice_id: str,
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> list[PaymentResponse]:
    """Fetch all payments received towards a specific invoice."""
    return payment_service.list_payments_for_invoice(invoice_id=invoice_id)


@router.post(
    "/invoices/detect-overdue",
    response_model=OverdueDetectionResponse,
    summary="Run overdue invoices scan job",
)
def detect_overdue_invoices(
    due_days: int = Query(
        30,
        ge=1,
        le=365,
        description="Days after invoice date when an unpaid invoice is marked overdue",
    ),
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: CurrentUser = Depends(require_permission("orders:manage")),
) -> OverdueDetectionResponse:
    """Scan and transition unpaid/partially-paid invoices past due window to overdue status."""
    return payment_service.detect_overdue_invoices(
        due_days=due_days,
        current_user=current_user,
    )


@router.post(
    "/invoices/{invoice_id}/generate-irn",
    response_model=EInvoiceGenerateResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate or retrieve official GST E-Invoice IRN and signed QR Code",
)
def generate_invoice_irn(
    invoice_id: str,
    force_sandbox: bool = Query(False, description="Force sandbox generation for testing"),
    einvoice_service: EinvoiceService = Depends(get_einvoice_service),
    current_user: CurrentUser = Depends(require_permission("orders:manage")),
) -> EInvoiceGenerateResponse:
    """Generate statutory 64-hex IRN, Acknowledgment Number, and signed QR Code."""
    return einvoice_service.generate_irn(
        invoice_id=invoice_id,
        force_sandbox=force_sandbox,
        current_user=current_user,
    )


@router.post(
    "/invoices/{invoice_id}/generate-eway-bill",
    response_model=EWayBillResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate 12-digit GST E-Way Bill for goods transit",
)
def generate_eway_bill(
    invoice_id: str,
    payload: EWayBillGenerateRequest,
    einvoice_service: EinvoiceService = Depends(get_einvoice_service),
    current_user: CurrentUser = Depends(require_permission("orders:manage")),
) -> EWayBillResponse:
    """Generate statutory 12-digit E-Way Bill Number and validity duration for goods movement."""
    return einvoice_service.generate_eway_bill(
        invoice_id=invoice_id,
        payload=payload,
        current_user=current_user,
    )


@router.get(
    "/invoices/{invoice_id}/pdf",
    status_code=status.HTTP_200_OK,
    summary="Download print-ready GST Tax Invoice PDF",
)
def download_invoice_pdf(
    invoice_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    export_service: ExportService = Depends(get_export_service),
) -> Response:
    """Generate and download print-ready statutory GST Tax Invoice PDF document."""
    pdf_bytes = export_service.generate_invoice_pdf(invoice_id=invoice_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="Invoice_{invoice_id}.pdf"'},
    )
