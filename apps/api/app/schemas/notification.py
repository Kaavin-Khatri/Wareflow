"""Notification request and response schemas."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class NotificationResponse(BaseModel):
    """Notification item representation."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Unique notification ID")
    user_id: str = Field(..., description="Recipient user ID")
    type: str = Field(..., description="Notification category/type")
    title: str = Field(..., description="Notification title")
    body: str = Field(..., description="Notification message body")
    is_read: bool = Field(..., description="Whether notification has been marked as read")
    created_at: datetime = Field(..., description="Timestamp notification was created")


class NotificationListResponse(BaseModel):
    """Paginated list of notifications with unread counts."""

    items: list[NotificationResponse] = Field(..., description="List of notification items")
    total: int = Field(..., description="Total notifications matching filter")
    unread_count: int = Field(..., description="Total unread notifications for the user")
    page: int = Field(1, description="Current page number")
    limit: int = Field(20, description="Items per page")


class NotificationReadResponse(BaseModel):
    """Response when marking notifications as read."""

    success: bool = Field(..., description="Whether operation succeeded")
    id: str | None = Field(None, description="ID of the marked notification")
    updated_count: int | None = Field(None, description="Number of notifications marked as read")
