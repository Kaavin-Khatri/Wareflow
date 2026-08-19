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


class NotificationPreferenceResponse(BaseModel):
    """Channel and category opt-in preferences for a user or retailer."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = Field("user", description="'user' or 'retailer'")
    entity_id: str = Field(..., description="Unique entity ID")
    in_app_enabled: bool = Field(True, description="In-app notification badge")
    email_enabled: bool = Field(True, description="Email alerts")
    whatsapp_enabled: bool = Field(True, description="WhatsApp template alerts")
    sms_enabled: bool = Field(False, description="SMS text alerts (opt-in)")
    critical_stock_sms: bool = Field(False, description="Receive SMS on low/critical stock")
    order_updates_sms: bool = Field(False, description="Receive SMS on order confirmation")
    dispatch_ready_sms: bool = Field(False, description="Receive SMS on PO dispatch ready")


class NotificationPreferenceUpdateRequest(BaseModel):
    """Payload to update notification channel preferences."""

    in_app_enabled: bool | None = None
    email_enabled: bool | None = None
    whatsapp_enabled: bool | None = None
    sms_enabled: bool | None = None
    critical_stock_sms: bool | None = None
    order_updates_sms: bool | None = None
    dispatch_ready_sms: bool | None = None
