"""FastAPI endpoints for Multi-Warehouse Stock & Batch Visibility."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.security import CurrentUser, get_current_user
from app.schemas.stock import (
    ProductStockResponse,
    StockBatchResponse,
    StockOverviewResponse,
    WarehouseSummary,
)
from app.services.stock_service import StockService

router = APIRouter(tags=["Stock & Inventory"])


def get_stock_service() -> StockService:
    from app.core.di import get_stock_service as di_get_stock_service

    return di_get_stock_service()


@router.get("/stock/overview", response_model=StockOverviewResponse)
def get_stock_overview(
    service: Annotated[StockService, Depends(get_stock_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    warehouse_id: Annotated[str | None, Query(description="Filter by warehouse ID")] = None,
    category_id: Annotated[str | None, Query(description="Filter by product category ID")] = None,
    status: Annotated[
        str | None, Query(description="Filter by status ('ok', 'low', 'critical')")
    ] = None,
    search: Annotated[
        str | None, Query(description="Search by product name, SKU, or barcode")
    ] = None,
) -> StockOverviewResponse:
    """
    Fetch multi-warehouse stock overview feed with health indicators
    and aggregate on-hand inventory metrics.
    """
    return service.get_stock_overview(
        warehouse_id=warehouse_id,
        category_id=category_id,
        status_filter=status,
        search=search,
    )


@router.get("/stock/warehouses", response_model=list[WarehouseSummary])
def list_warehouses(
    service: Annotated[StockService, Depends(get_stock_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    active_only: Annotated[bool, Query(description="Return only active warehouses")] = True,
) -> list[WarehouseSummary]:
    """List all registered warehouse facilities."""
    return service.list_warehouses(active_only=active_only)


@router.get("/stock/expiring", response_model=list[StockBatchResponse])
def get_expiring_batches(
    service: Annotated[StockService, Depends(get_stock_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    days: Annotated[int, Query(ge=1, le=365, description="Expiry window in days")] = 30,
    warehouse_id: Annotated[str | None, Query(description="Filter by warehouse ID")] = None,
) -> list[StockBatchResponse]:
    """Retrieve stock batches expiring within the specified number of days."""
    return service.get_batches_expiring_soon(days=days, warehouse_id=warehouse_id)


@router.get("/products/{product_id}/stock", response_model=ProductStockResponse)
def get_product_stock(
    product_id: str,
    service: Annotated[StockService, Depends(get_stock_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    warehouse_id: Annotated[
        str | None, Query(description="Filter batches by specific warehouse")
    ] = None,
) -> ProductStockResponse:
    """Retrieve detailed multi-warehouse stock breakdown and batch list for a single product."""
    return service.get_product_stock(product_id=product_id, warehouse_id=warehouse_id)
