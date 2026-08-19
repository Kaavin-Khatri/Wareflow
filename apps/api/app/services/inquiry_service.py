"""
Product inquiry service.

Manages the lifecycle of customer and retailer product inquiries and quote requests,
including submission from the retailer portal, staff responses, and notification triggers.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from fastapi import HTTPException, status

if TYPE_CHECKING:
    from app.core.security import CurrentUser

from app.models.portal import InquiryStatusEnum, ProductInquiry
from app.repositories.interfaces.inquiry_repository import InquiryRepositoryInterface
from app.repositories.interfaces.product_repository import ProductRepositoryInterface
from app.schemas.inquiries import (
    CreateInquiryRequest,
    ProductInquiryResponse,
    RespondInquiryRequest,
)
from app.services.notification_service import NotificationService


class InquiryService:
    """Service handling product inquiry submissions, staff inbox, and notifications."""

    def __init__(
        self,
        inquiry_repo: InquiryRepositoryInterface,
        product_repo: ProductRepositoryInterface,
        notification_service: NotificationService,
    ) -> None:
        self._inquiry_repo = inquiry_repo
        self._product_repo = product_repo
        self._notif_service = notification_service

    def create_retailer_inquiry(
        self,
        current_user: CurrentUser,
        payload: CreateInquiryRequest,
    ) -> ProductInquiryResponse:
        """Create a new product inquiry submitted by a logged-in retailer."""
        if not current_user.retailer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Retailer identity required to submit a portal inquiry.",
            )

        product = self._product_repo.get_by_id(payload.product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found.",
            )

        inquiry = ProductInquiry(
            product_id=payload.product_id,
            retailer_id=current_user.retailer_id,
            message=payload.message,
            status=InquiryStatusEnum.OPEN,
            created_at=datetime.now(timezone.utc),
        )
        saved = self._inquiry_repo.create(inquiry)
        return self._to_response(saved, product=product)

    def list_retailer_inquiries(
        self,
        current_user: CurrentUser,
    ) -> list[ProductInquiryResponse]:
        """List inquiries strictly for the authenticated retailer in chronological order."""
        if not current_user.retailer_id:
            return []
        items = self._inquiry_repo.list_for_retailer(current_user.retailer_id)
        return [self._to_response(item) for item in items]

    def list_staff_inquiries(
        self,
        status_filter: str | None = None,
        product_id: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ProductInquiryResponse]:
        """List product inquiries for staff with optional status/product filters."""
        items = self._inquiry_repo.list_all(
            status=status_filter,
            product_id=product_id,
            skip=skip,
            limit=limit,
        )
        return [self._to_response(item) for item in items]

    def respond_to_inquiry(
        self,
        inquiry_id: str,
        payload: RespondInquiryRequest,
        current_user: CurrentUser,
    ) -> ProductInquiryResponse:
        """Staff responds to an inquiry and fires notification to the retailer."""
        inquiry = self._inquiry_repo.get_by_id(inquiry_id)
        if not inquiry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inquiry not found.",
            )

        inquiry.response = payload.response
        inquiry.status = InquiryStatusEnum.RESPONDED
        inquiry.responded_at = datetime.now(timezone.utc)
        updated = self._inquiry_repo.update(inquiry)

        product_name = getattr(inquiry.product, "name", "Requested Item") if getattr(inquiry, "product", None) else "Requested Item"

        # Dispatch notification to retailer via NotificationService
        if inquiry.retailer_id:
            self._notif_service.notify_retailer_inquiry_responded(
                retailer_id=inquiry.retailer_id,
                product_name=product_name,
                response_text=payload.response,
            )

        return self._to_response(updated)

    def _to_response(
        self,
        inquiry: ProductInquiry,
        product: object | None = None,
    ) -> ProductInquiryResponse:
        """Map ORM ProductInquiry to response schema."""
        prod = product or getattr(inquiry, "product", None)
        retailer = getattr(inquiry, "retailer", None)

        if isinstance(prod, dict):
            p_name = prod.get("name", "Unknown Product")
            p_sku = prod.get("sku", "N/A")
        elif prod is not None:
            p_name = getattr(prod, "name", "Unknown Product")
            p_sku = getattr(prod, "sku", "N/A")
        else:
            p_name = "Unknown Product"
            p_sku = "N/A"

        r_name = (getattr(retailer, "name", None) or getattr(retailer, "business_name", None)) if retailer else None

        return ProductInquiryResponse(
            id=inquiry.id or "",
            product_id=inquiry.product_id,
            product_name=p_name,
            product_sku=p_sku,
            retailer_id=inquiry.retailer_id,
            retailer_name=r_name,
            customer_id=inquiry.customer_id,
            message=inquiry.message,
            status=inquiry.status.value if hasattr(inquiry.status, "value") else str(inquiry.status),
            response=inquiry.response,
            created_at=inquiry.created_at or datetime.now(timezone.utc),
            responded_at=inquiry.responded_at,
        )
