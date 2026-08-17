"""Retailer account router."""

from fastapi import APIRouter, Depends, Query, status

from app.core.di import get_retailer_service
from app.core.security import CurrentUser, get_current_user, require_permission
from app.schemas.retailers import RetailerCreditLimitUpdateRequest, RetailerResponse
from app.services.retailer_service import RetailerService

router = APIRouter(prefix="/retailers", tags=["Retailers"])


@router.get(
    "",
    response_model=list[RetailerResponse],
    status_code=status.HTTP_200_OK,
    summary="List wholesale retailers",
)
def list_retailers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    current_user: CurrentUser = Depends(get_current_user),
    service: RetailerService = Depends(get_retailer_service),
) -> list[RetailerResponse]:
    """Retrieve wholesale retailers and credit limits."""
    items = service.list_retailers(skip=skip, limit=limit)
    return [RetailerResponse.model_validate(r) for r in items]


@router.patch(
    "/{retailer_id}/credit-limit",
    response_model=RetailerResponse,
    status_code=status.HTTP_200_OK,
    summary="Update retailer credit limit",
)
def update_retailer_credit_limit(
    retailer_id: str,
    payload: RetailerCreditLimitUpdateRequest,
    current_user: CurrentUser = Depends(require_permission("settings:manage")),
    service: RetailerService = Depends(get_retailer_service),
) -> RetailerResponse:
    """Update authorized credit limit for a retailer and log the change."""
    updated = service.update_credit_limit(
        retailer_id=retailer_id,
        new_credit_limit=payload.credit_limit,
        actor_id=current_user.id,
    )
    return RetailerResponse.model_validate(updated)
