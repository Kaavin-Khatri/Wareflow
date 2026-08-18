"""Business settings and compliance profile API router."""

from fastapi import APIRouter, Depends

from app.core.di import get_business_settings_service
from app.core.security import CurrentUser, get_current_user, require_permission
from app.schemas.business_settings import (
    BusinessSettingsResponse,
    BusinessSettingsUpdateRequest,
)
from app.services.business_settings_service import BusinessSettingsService

router = APIRouter(prefix="/settings/business", tags=["Business Settings"])


@router.get(
    "",
    response_model=BusinessSettingsResponse,
    summary="Get distributor business profile and FSSAI compliance metadata",
)
def get_business_settings(
    settings_service: BusinessSettingsService = Depends(get_business_settings_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> BusinessSettingsResponse:
    """Retrieve the legal business name, GSTIN, and FSSAI license status."""
    return settings_service.get_settings()


@router.put(
    "",
    response_model=BusinessSettingsResponse,
    summary="Update distributor business settings and compliance profile",
)
def update_business_settings(
    payload: BusinessSettingsUpdateRequest,
    settings_service: BusinessSettingsService = Depends(get_business_settings_service),
    current_user: CurrentUser = Depends(require_permission("settings:manage")),
) -> BusinessSettingsResponse:
    """Update distributor profile and FSSAI license certificate details."""
    return settings_service.update_settings(payload=payload, actor_id=current_user.id)
