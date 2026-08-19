"""Retailer account and pricing tier router."""

from fastapi import APIRouter, Depends, Query, status

from app.core.di import get_ledger_service, get_retailer_service
from app.core.security import CurrentUser, get_current_user, require_permission
from app.schemas.billing import RetailerLedgerResponse
from app.schemas.retailers import (
    RetailerCreateRequest,
    RetailerCreditLimitUpdateRequest,
    RetailerInviteRequest,
    RetailerInviteResponse,
    RetailerResponse,
    RetailerUpdateRequest,
)
from app.services.ledger_service import LedgerService
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
    is_active: bool | None = Query(None, description="Filter by active status"),
    search: str | None = Query(
        None, description="Search query by name, contact, phone, email, or GSTIN"
    ),
    current_user: CurrentUser = Depends(get_current_user),
    service: RetailerService = Depends(get_retailer_service),
) -> list[RetailerResponse]:
    """Retrieve wholesale retailers with optional search and active status filters."""
    items = service.list_retailers(skip=skip, limit=limit, is_active=is_active, search=search)
    return [RetailerResponse.model_validate(r) for r in items]


@router.post(
    "",
    response_model=RetailerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a wholesale retailer",
)
def create_retailer(
    payload: RetailerCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: RetailerService = Depends(get_retailer_service),
) -> RetailerResponse:
    """Register a new B2B wholesale retailer account with initial pricing tier and credit limit."""
    created = service.create_retailer(payload=payload, actor_id=current_user.id)
    return RetailerResponse.model_validate(created)


@router.get(
    "/{retailer_id}",
    response_model=RetailerResponse,
    status_code=status.HTTP_200_OK,
    summary="Get retailer profile by ID",
)
def get_retailer(
    retailer_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: RetailerService = Depends(get_retailer_service),
) -> RetailerResponse:
    """Retrieve a single wholesale retailer by UUID."""
    retailer = service.get_retailer(retailer_id=retailer_id)
    return RetailerResponse.model_validate(retailer)


@router.patch(
    "/{retailer_id}",
    response_model=RetailerResponse,
    status_code=status.HTTP_200_OK,
    summary="Update retailer profile and pricing tier",
)
def update_retailer(
    retailer_id: str,
    payload: RetailerUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: RetailerService = Depends(get_retailer_service),
) -> RetailerResponse:
    """Update retailer contact info, pricing tier, active status, or credit limit."""
    updated = service.update_retailer(
        retailer_id=retailer_id,
        payload=payload,
        actor_id=current_user.id,
    )
    return RetailerResponse.model_validate(updated)


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


@router.get(
    "/{retailer_id}/ledger",
    response_model=RetailerLedgerResponse,
    status_code=status.HTTP_200_OK,
    summary="Get retailer accounts-receivable chronological ledger statement",
)
def get_retailer_ledger(
    retailer_id: str,
    ledger_service: LedgerService = Depends(get_ledger_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> RetailerLedgerResponse:
    """
    Fetch a complete chronological accounts-receivable statement.

    Each invoice is a debit charge (+), each payment is a credit settlement (-),
    and the final running balance exactly matches retailer.credit_balance.
    """
    return ledger_service.get_retailer_ledger(retailer_id=retailer_id)


@router.post(
    "/{retailer_id}/invite-portal-access",
    response_model=RetailerInviteResponse,
    status_code=status.HTTP_200_OK,
    summary="Issue self-service portal invite link for a retailer",
)
def invite_retailer_portal_access(
    retailer_id: str,
    payload: RetailerInviteRequest,
    current_user: CurrentUser = Depends(require_permission("retailers:manage")),
    service: RetailerService = Depends(get_retailer_service),
) -> RetailerInviteResponse:
    """
    Generate portal access invitation and provision Firebase user credentials.

    Restricted to Owner/Manager administrative staff.
    """
    return service.invite_portal_access(
        retailer_id=retailer_id,
        payload=payload,
        actor_id=current_user.id,
    )

