"""Supplier Self-Service Portal router (Public, Token-Authenticated via URL)."""

from fastapi import APIRouter, Depends, status

from app.core.di import get_supplier_portal_service
from app.schemas.supplier_portal import ReadyForDispatchResponse, SupplierPortalPOResponse
from app.services.supplier_portal_service import SupplierPortalService

router = APIRouter(prefix="/supplier-portal", tags=["Supplier Portal"])


@router.get(
    "/{token}",
    response_model=SupplierPortalPOResponse,
    status_code=status.HTTP_200_OK,
    summary="Get purchase order details via supplier magic link",
)
def get_purchase_order_by_token(
    token: str,
    service: SupplierPortalService = Depends(get_supplier_portal_service),
) -> SupplierPortalPOResponse:
    """Public read-only view of a Purchase Order for supplier verification."""
    return service.get_po_by_token(token_str=token)


@router.post(
    "/{token}/ready-for-dispatch",
    response_model=ReadyForDispatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark purchase order ready for dispatch via supplier magic link",
)
def mark_purchase_order_ready_for_dispatch(
    token: str,
    service: SupplierPortalService = Depends(get_supplier_portal_service),
) -> ReadyForDispatchResponse:
    """Supplier action marking consignment ready for pickup/dispatch and notifying purchasing staff."""
    return service.mark_ready_for_dispatch(token_str=token)
