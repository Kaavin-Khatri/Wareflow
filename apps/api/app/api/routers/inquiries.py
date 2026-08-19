"""Product inquiry management router for warehouse and sales staff."""

from fastapi import APIRouter, Depends, status

from app.core.di import get_inquiry_service
from app.core.security import CurrentUser, require_staff
from app.schemas.inquiries import ProductInquiryResponse, RespondInquiryRequest
from app.services.inquiry_service import InquiryService

router = APIRouter(prefix="/inquiries", tags=["Product Inquiries (Staff)"])


@router.get(
    "",
    response_model=list[ProductInquiryResponse],
    status_code=status.HTTP_200_OK,
    summary="List all product inquiries (Staff Inbox)",
)
def list_inquiries(
    status_filter: str | None = None,
    product_id: str | None = None,
    skip: int = 0,
    limit: int = 50,
    current_user: CurrentUser = Depends(require_staff),
    service: InquiryService = Depends(get_inquiry_service),
) -> list[ProductInquiryResponse]:
    """Retrieve all product inquiries with optional status/product filtering."""
    return service.list_staff_inquiries(
        status_filter=status_filter,
        product_id=product_id,
        skip=skip,
        limit=limit,
    )


@router.patch(
    "/{inquiry_id}/respond",
    response_model=ProductInquiryResponse,
    status_code=status.HTTP_200_OK,
    summary="Respond to a product inquiry and notify the retailer",
)
def respond_to_inquiry(
    inquiry_id: str,
    body: RespondInquiryRequest,
    current_user: CurrentUser = Depends(require_staff),
    service: InquiryService = Depends(get_inquiry_service),
) -> ProductInquiryResponse:
    """Record staff response, update status to responded, and dispatch notification."""
    return service.respond_to_inquiry(
        inquiry_id=inquiry_id,
        payload=body,
        current_user=current_user,
    )
