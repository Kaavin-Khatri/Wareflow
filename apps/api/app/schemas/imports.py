"""Pydantic schemas for bulk CSV product import and export operations."""

from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field


class ProductImportRow(BaseModel):
    """Normalized and validated product row from CSV."""

    sku: str = Field(..., min_length=1, max_length=100, description="Unique product SKU")
    name: str = Field(..., min_length=1, max_length=255, description="Product title")
    wholesale_price: Decimal = Field(..., ge=0, description="Selling wholesale price per base unit")
    cost_price: Decimal = Field(default=Decimal("0.00"), ge=0, description="Purchase cost price")
    category_name: str | None = Field(default=None, max_length=100, description="Category name")
    unit: str | None = Field(default="Piece", max_length=50, description="Base unit of measure")
    hsn_code: str | None = Field(default=None, max_length=20, description="HSN/SAC code for GST")
    barcode: str | None = Field(default=None, max_length=100, description="EAN/UPC barcode")
    reorder_point: int = Field(default=10, ge=0, description="Low stock threshold")
    reorder_qty: int = Field(default=50, ge=1, description="Default reorder batch quantity")
    description: str | None = Field(default=None, max_length=1000, description="Product description")


class ProductImportRowPreview(BaseModel):
    """Dry-run preview item for user inspection before commit."""

    row_number: int = Field(..., description="1-indexed line number in uploaded CSV")
    action: Literal["create", "update", "reject"] = Field(
        ..., description="Action to be performed or rejection status"
    )
    sku: str = Field(..., description="Product SKU code")
    name: str = Field(default="", description="Product display name")
    wholesale_price: float | None = Field(default=None, description="Wholesale price")
    cost_price: float | None = Field(default=None, description="Cost price")
    category_name: str | None = Field(default=None, description="Category name")
    unit: str | None = Field(default=None, description="Base UoM")
    hsn_code: str | None = Field(default=None, description="HSN code")
    barcode: str | None = Field(default=None, description="Barcode or auto-generated indication")
    errors: list[str] = Field(default_factory=list, description="Validation failure reasons if rejected")


class ProductImportSummary(BaseModel):
    """Aggregated metrics for CSV batch import."""

    total_rows: int = Field(..., description="Total rows in CSV payload excluding header")
    valid_count: int = Field(..., description="Total valid rows eligible for processing")
    create_count: int = Field(..., description="Number of new products to create")
    update_count: int = Field(..., description="Number of existing products to update")
    reject_count: int = Field(..., description="Number of invalid rows with validation errors")


class ProductImportResponse(BaseModel):
    """Response returned for dry-run preview and committed imports."""

    dry_run: bool = Field(..., description="True if dry-run validation only; False if committed")
    summary: ProductImportSummary = Field(..., description="Batch summary counts")
    rows: list[ProductImportRowPreview] = Field(..., description="Row-by-row breakdown")
