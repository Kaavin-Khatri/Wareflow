"""Search request and response schemas."""

from pydantic import BaseModel, Field


class SearchResultItem(BaseModel):
    """A single unified search result item across ERP domains."""

    id: str = Field(..., description="Unique entity identifier")
    kind: str = Field(
        ...,
        description="Entity kind: product, sales_order, purchase_order, retailer, supplier, invoice",
    )
    title: str = Field(..., description="Primary headline (Name, SKU, or Order/Invoice number)")
    subtitle: str | None = Field(
        None, description="Secondary description, details, price, or party name"
    )
    badge: str | None = Field(None, description="Status badge or category descriptor")
    url: str = Field(..., description="Direct frontend navigation path")
    score: float = Field(0.0, description="Relevance ranking score")


class SearchResponse(BaseModel):
    """Unified search endpoint response."""

    query: str = Field(..., description="Normalized query string")
    total: int = Field(..., description="Total matched items")
    results: list[SearchResultItem] = Field(default_factory=list, description="Ranked search results")
