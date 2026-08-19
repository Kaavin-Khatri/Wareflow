"""Delivery dispatch and logistics schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.delivery import DeliveryStatusEnum


class DeliveryAssignRequest(BaseModel):
    """Schema for assigning driver and vehicle to a packed sales order."""

    driver_name: str = Field(..., min_length=1, max_length=100, description="Assigned driver name")
    vehicle_no: str = Field(..., min_length=1, max_length=50, description="Vehicle registration number")
    notes: str | None = Field(None, max_length=500, description="Dispatch instructions or notes")


class DeliveryStatusUpdateRequest(BaseModel):
    """Schema for updating delivery transit status."""

    status: DeliveryStatusEnum = Field(..., description="Target delivery status")
    notes: str | None = Field(
        None, max_length=500, description="Delivery notes (mandatory if status is 'failed')"
    )


class DeliveryResponse(BaseModel):
    """Schema for delivery record response."""

    id: str
    sales_order_id: str
    so_number: str | None = None
    buyer_name: str | None = None
    destination_address: str | None = None
    driver_name: str | None = None
    vehicle_no: str | None = None
    status: DeliveryStatusEnum
    total_amount: float | None = None
    dispatched_at: datetime | None = None
    delivered_at: datetime | None = None
    notes: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
