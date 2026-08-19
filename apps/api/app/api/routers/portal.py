"""Retailer Self-Service Portal API router with server-side tenant scoping."""

from typing import Any

from fastapi import APIRouter, Depends, status

from app.core.di import get_inquiry_service, get_ledger_service, get_portal_auth_service
from app.core.security import CurrentUser, get_current_user_claims, require_portal_retailer
from app.schemas.billing import RetailerLedgerResponse
from app.schemas.inquiries import CreateInquiryRequest, ProductInquiryResponse
from app.schemas.invoices import InvoiceResponse
from app.schemas.portal import (
    PortalBootstrapRequest,
    PortalCatalogProductResponse,
    PortalCategoryResponse,
    PortalInvoiceListItemResponse,
    PortalOrderListItemResponse,
    RetailerPortalMeResponse,
)
from app.schemas.sales_orders import SalesOrderResponse
from app.services.inquiry_service import InquiryService
from app.services.ledger_service import LedgerService
from app.services.portal_auth_service import PortalAuthService

router = APIRouter(prefix="/portal", tags=["Retailer Portal"])


@router.get(
    "/catalog",
    response_model=list[PortalCatalogProductResponse],
    status_code=status.HTTP_200_OK,
    summary="Get wholesale product catalog customized to retailer pricing tier",
)
def get_retailer_catalog(
    category_id: str | None = None,
    search: str | None = None,
    skip: int = 0,
    limit: int = 100,
    current_user: CurrentUser = Depends(require_portal_retailer),
    service: PortalAuthService = Depends(get_portal_auth_service),
) -> list[PortalCatalogProductResponse]:
    """Retrieve tier-priced product catalog with privacy-preserving availability bands."""
    return service.get_retailer_catalog(
        current_user=current_user,
        category_id=category_id,
        search=search,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/categories",
    response_model=list[PortalCategoryResponse],
    status_code=status.HTTP_200_OK,
    summary="Get product categories for catalog filtering",
)
def get_catalog_categories(
    current_user: CurrentUser = Depends(require_portal_retailer),
    service: PortalAuthService = Depends(get_portal_auth_service),
) -> list[PortalCategoryResponse]:
    """Retrieve product categories available in catalog."""
    return service.get_catalog_categories(current_user=current_user)


@router.post(
    "/auth/bootstrap",
    response_model=RetailerPortalMeResponse,
    status_code=status.HTTP_200_OK,
    summary="Onboard or authenticate retailer portal user",
)
def bootstrap_retailer(
    body: PortalBootstrapRequest | None = None,
    claims: dict[str, Any] = Depends(get_current_user_claims),
    service: PortalAuthService = Depends(get_portal_auth_service),
) -> RetailerPortalMeResponse:
    """
    Onboard authenticated Firebase retailer user.

    Validates that user is not staff, and binds to retailer account via email/token.
    """
    return service.bootstrap_retailer_user(
        uid=claims["uid"],
        email=claims.get("email", ""),
        invite_token=body.invite_token if body else None,
        display_name=body.display_name if body and body.display_name else claims.get("name"),
        phone=body.phone if body and body.phone else claims.get("phone_number"),
    )


@router.get(
    "/me",
    response_model=RetailerPortalMeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get authenticated retailer company and credit profile",
)
def get_my_retailer_profile(
    current_user: CurrentUser = Depends(require_portal_retailer),
    service: PortalAuthService = Depends(get_portal_auth_service),
) -> RetailerPortalMeResponse:
    """Retrieve retailer business metadata and credit limit status."""
    return service.get_portal_me(current_user)


@router.get(
    "/orders",
    response_model=list[PortalOrderListItemResponse],
    status_code=status.HTTP_200_OK,
    summary="List orders placed by this retailer",
)
def list_my_orders(
    current_user: CurrentUser = Depends(require_portal_retailer),
    service: PortalAuthService = Depends(get_portal_auth_service),
) -> list[PortalOrderListItemResponse]:
    """Retrieve sales orders strictly scoped to the authenticated retailer."""
    return service.list_retailer_orders(current_user)


@router.get(
    "/orders/{order_id}",
    response_model=SalesOrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Get order details with strict retailer tenant isolation",
)
def get_my_order(
    order_id: str,
    current_user: CurrentUser = Depends(require_portal_retailer),
    service: PortalAuthService = Depends(get_portal_auth_service),
) -> SalesOrderResponse:
    """Retrieve single sales order details. Rejects cross-retailer access with 403 Forbidden."""
    order = service.get_retailer_order(order_id=order_id, current_user=current_user)
    return SalesOrderResponse.model_validate(order)


@router.get(
    "/invoices",
    response_model=list[PortalInvoiceListItemResponse],
    status_code=status.HTTP_200_OK,
    summary="List GST invoices issued to this retailer",
)
def list_my_invoices(
    current_user: CurrentUser = Depends(require_portal_retailer),
    service: PortalAuthService = Depends(get_portal_auth_service),
) -> list[PortalInvoiceListItemResponse]:
    """Retrieve invoices strictly scoped to the authenticated retailer."""
    return service.list_retailer_invoices(current_user)


@router.get(
    "/invoices/{invoice_id}",
    response_model=InvoiceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get invoice details with strict retailer tenant isolation",
)
def get_my_invoice(
    invoice_id: str,
    current_user: CurrentUser = Depends(require_portal_retailer),
    service: PortalAuthService = Depends(get_portal_auth_service),
) -> InvoiceResponse:
    """Retrieve invoice details. Rejects cross-retailer access with 403 Forbidden."""
    invoice = service.get_retailer_invoice(invoice_id=invoice_id, current_user=current_user)
    return InvoiceResponse.model_validate(invoice)


@router.get(
    "/ledger",
    response_model=RetailerLedgerResponse,
    status_code=status.HTTP_200_OK,
    summary="Get accounts-receivable statement for this retailer",
)
def get_my_ledger(
    current_user: CurrentUser = Depends(require_portal_retailer),
    ledger_service: LedgerService = Depends(get_ledger_service),
) -> RetailerLedgerResponse:
    """Retrieve full chronological AR statement scoped to current retailer."""
    if not current_user.retailer_id:
        raise ValueError("Retailer ID is missing from user context.")
    return ledger_service.get_retailer_ledger(retailer_id=current_user.retailer_id)


@router.post(
    "/inquiries",
    response_model=ProductInquiryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a product inquiry or bulk quote request",
)
def create_portal_inquiry(
    body: CreateInquiryRequest,
    current_user: CurrentUser = Depends(require_portal_retailer),
    inquiry_service: InquiryService = Depends(get_inquiry_service),
) -> ProductInquiryResponse:
    """Create a new product inquiry from the retailer portal."""
    return inquiry_service.create_retailer_inquiry(
        current_user=current_user,
        payload=body,
    )


@router.get(
    "/inquiries",
    response_model=list[ProductInquiryResponse],
    status_code=status.HTTP_200_OK,
    summary="List inquiries submitted by this retailer",
)
def list_my_inquiries(
    current_user: CurrentUser = Depends(require_portal_retailer),
    inquiry_service: InquiryService = Depends(get_inquiry_service),
) -> list[ProductInquiryResponse]:
    """Retrieve product inquiries strictly scoped to the authenticated retailer."""
    return inquiry_service.list_retailer_inquiries(current_user=current_user)

