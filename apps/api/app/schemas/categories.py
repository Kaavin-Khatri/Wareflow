"""Category Pydantic request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreateRequest(BaseModel):
    """Payload for creating a product category."""

    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    parent_id: str | None = Field(default=None, description="Optional parent category UUID")


class CategoryUpdateRequest(BaseModel):
    """Payload for updating an existing product category."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    parent_id: str | None = None


class CategoryResponse(BaseModel):
    """Serialised category representation."""

    id: str
    name: str
    parent_id: str | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
