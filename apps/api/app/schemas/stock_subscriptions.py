"""Pydantic schemas for Stock Subscriptions (Step 13.4)."""

from datetime import datetime
from pydantic import BaseModel, Field

from app.models.portal import ChannelPreferenceEnum


class RetailerSubscribeRequest(BaseModel):
    """Payload to subscribe a retailer to product restock alerts."""

    retailer_id: str = Field(..., description="Retailer UUID")
    channel_preference: ChannelPreferenceEnum = Field(
        default=ChannelPreferenceEnum.BOTH,
        description="Notification channel preference: whatsapp, email, or both",
    )


class StockSubscriptionResponse(BaseModel):
    """Response model for a stock subscription."""

    id: str
    retailer_id: str
    product_id: str
    product_name: str | None = None
    retailer_name: str | None = None
    channel_preference: str
    is_active: bool
    created_at: datetime
    notified_at: datetime | None = None

    model_config = {"from_attributes": True}


class RetailerSubscriptionCountResponse(BaseModel):
    """Active subscription count per retailer."""

    retailer_id: str
    active_subscriptions_count: int
