"""Notification management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.di import (
    get_notification_preference_service,
    get_notification_service,
)
from app.core.security import CurrentUser, get_current_user
from app.schemas.notification import (
    NotificationListResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdateRequest,
    NotificationReadResponse,
    NotificationResponse,
)
from app.services.notification_preference_service import NotificationPreferenceService
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/preferences", response_model=NotificationPreferenceResponse)
def get_notification_preferences(
    current_user: CurrentUser = Depends(get_current_user),
    service: NotificationPreferenceService = Depends(get_notification_preference_service),
) -> NotificationPreferenceResponse:
    """Get notification channel opt-in preferences for current user."""
    return service.get_preferences(entity_type="user", entity_id=current_user.id)


@router.put("/preferences", response_model=NotificationPreferenceResponse)
def update_notification_preferences(
    payload: NotificationPreferenceUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: NotificationPreferenceService = Depends(get_notification_preference_service),
) -> NotificationPreferenceResponse:
    """Update notification channel opt-in preferences for current user."""
    return service.update_preferences(
        entity_type="user", entity_id=current_user.id, payload=payload
    )


@router.get("/preferences/{entity_type}/{entity_id}", response_model=NotificationPreferenceResponse)
def get_entity_notification_preferences(
    entity_type: str,
    entity_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: NotificationPreferenceService = Depends(get_notification_preference_service),
) -> NotificationPreferenceResponse:
    """Get notification channel preferences for a specific entity (e.g. retailer)."""
    return service.get_preferences(entity_type=entity_type, entity_id=entity_id)


@router.put("/preferences/{entity_type}/{entity_id}", response_model=NotificationPreferenceResponse)
def update_entity_notification_preferences(
    entity_type: str,
    entity_id: str,
    payload: NotificationPreferenceUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: NotificationPreferenceService = Depends(get_notification_preference_service),
) -> NotificationPreferenceResponse:
    """Update notification channel preferences for a specific entity (e.g. retailer)."""
    return service.update_preferences(
        entity_type=entity_type, entity_id=entity_id, payload=payload
    )


@router.get("", response_model=NotificationListResponse)
def list_notifications(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    unread_only: bool = Query(False, description="Filter unread only"),
    current_user: CurrentUser = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationListResponse:
    """List paginated notifications for the authenticated user."""
    items, total, unread_count = service.list_user_notifications(
        user_id=current_user.id,
        unread_only=unread_only,
        page=page,
        limit=limit,
    )
    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in items],
        total=total,
        unread_count=unread_count,
        page=page,
        limit=limit,
    )


@router.patch("/read-all", response_model=NotificationReadResponse)
def mark_all_as_read(
    current_user: CurrentUser = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationReadResponse:
    """Mark all unread notifications as read for current user."""
    count = service.mark_all_notifications_read(user_id=current_user.id)
    return NotificationReadResponse(success=True, updated_count=count)


@router.patch("/{id}/read", response_model=NotificationReadResponse)
def mark_notification_read(
    id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationReadResponse:
    """Mark a specific notification as read."""
    success = service.mark_notification_read(notification_id=id, user_id=current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification '{id}' not found for user",
        )
    return NotificationReadResponse(success=True, id=id)
