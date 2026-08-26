from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Response, status

from app.core.di import (
    get_export_service,
    get_recall_service,
    get_stock_service,
    get_transfer_service,
)
from app.core.security import CurrentUser, get_current_user, require_permission
from app.schemas.recalls import (
    BatchRecallCreateRequest,
    BatchRecallListResponse,
    BatchRecallNotifyResponse,
    BatchRecallResponse,
)
from app.schemas.stock import (
    ProductStockResponse,
    StockBatchResponse,
    StockOverviewResponse,
    WarehouseSummary,
)
from app.schemas.stock_adjustments import (
    StockAdjustmentCreateRequest,
    StockAdjustmentResponse,
    StockMovementListResponse,
)
from app.schemas.stock_transfers import (
    StockTransferCreateRequest,
    StockTransferListResponse,
    StockTransferResponse,
)
from app.services.export_service import ExportService
from app.services.stock_service import StockService

router = APIRouter(tags=["Stock & Inventory"])


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


@router.get(
    "/stock/overview.xlsx",
    status_code=status.HTTP_200_OK,
    summary="Download stock overview Excel workbook",
)
def download_stock_overview_excel(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    export_service: Annotated[ExportService, Depends(get_export_service)],
) -> Response:
    """Generate and download structured Stock Valuation & Inventory Overview Excel spreadsheet."""
    xlsx_bytes = export_service.generate_stock_overview_excel()
    dt_str = datetime.now().strftime("%Y%m%d")
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="stock_overview_{dt_str}.xlsx"'},
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


@router.get("/stock/batches", response_model=list[StockBatchResponse])
def list_stock_batches(
    service: Annotated[StockService, Depends(get_stock_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    product_id: Annotated[str | None, Query(description="Filter by product ID")] = None,
    warehouse_id: Annotated[str | None, Query(description="Filter by warehouse ID")] = None,
) -> list[StockBatchResponse]:
    """Retrieve active stock batches across products and storage warehouses."""
    return service.list_active_batches(product_id=product_id, warehouse_id=warehouse_id)


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


@router.post(
    "/stock/adjustments",
    response_model=StockAdjustmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def adjust_stock(
    payload: StockAdjustmentCreateRequest,
    service: Annotated[StockService, Depends(get_stock_service)],
    current_user: Annotated[CurrentUser, Depends(require_permission("inventory:manage"))],
) -> StockAdjustmentResponse:
    """
    Record a manual stock adjustment with mandatory reason and non-negative batch guarantee.
    'recount' reason strictly requires the 'stock.recount' permission.
    """
    return service.adjust_stock(payload=payload, current_user=current_user)


@router.get("/stock/movements", response_model=StockMovementListResponse)
def list_stock_movements(
    service: Annotated[StockService, Depends(get_stock_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=200, description="Items per page")] = 50,
    product_id: Annotated[str | None, Query(description="Filter by product ID")] = None,
    warehouse_id: Annotated[str | None, Query(description="Filter by warehouse ID")] = None,
    type: Annotated[
        str | None,
        Query(
            description="Filter by movement type ('in', 'out', 'adjustment', 'return_in', 'return_out')"
        ),
    ] = None,
    start_date: Annotated[datetime | None, Query(description="Start date filter")] = None,
    end_date: Annotated[datetime | None, Query(description="End date filter")] = None,
    search: Annotated[
        str | None, Query(description="Search query (product name, SKU, reference)")
    ] = None,
) -> StockMovementListResponse:
    """
    Fetch paginated, filterable stock movements ledger joined with contextual human labels.
    """
    return service.list_movements(
        page=page,
        page_size=page_size,
        product_id=product_id,
        warehouse_id=warehouse_id,
        movement_type=type,
        start_date=start_date,
        end_date=end_date,
        search=search,
    )


@router.get(
    "/stock/movements.xlsx",
    status_code=status.HTTP_200_OK,
    summary="Download stock movements ledger Excel workbook",
)
def download_stock_movements_excel(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    export_service: Annotated[ExportService, Depends(get_export_service)],
) -> Response:
    """Generate and download structured Stock Movement Ledger Excel spreadsheet."""
    xlsx_bytes = export_service.generate_stock_movements_excel()
    dt_str = datetime.now().strftime("%Y%m%d")
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="stock_movements_{dt_str}.xlsx"'},
    )


@router.post(
    "/stock/transfers",
    response_model=StockTransferResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_stock_transfer(
    payload: StockTransferCreateRequest,
    service: Annotated[Any, Depends(get_transfer_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> StockTransferResponse:
    """
    Execute an atomic inter-warehouse stock transfer:
    - Decrements source batch and creates OUT movement
    - Creates or increments destination batch and creates IN movement
    - Blocked if source batch stock is insufficient (422)
    """
    return service.execute_transfer(payload=payload, current_user=current_user)


@router.get("/stock/transfers", response_model=StockTransferListResponse)
def list_stock_transfers(
    service: Annotated[Any, Depends(get_transfer_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=200, description="Items per page")] = 50,
    product_id: Annotated[str | None, Query(description="Filter by product ID")] = None,
    from_warehouse_id: Annotated[
        str | None, Query(description="Filter by source warehouse")
    ] = None,
    to_warehouse_id: Annotated[
        str | None, Query(description="Filter by destination warehouse")
    ] = None,
    start_date: Annotated[datetime | None, Query(description="Start date filter")] = None,
    end_date: Annotated[datetime | None, Query(description="End date filter")] = None,
    search: Annotated[str | None, Query(description="Search query")] = None,
) -> StockTransferListResponse:
    """
    Fetch paginated, filterable historical inter-warehouse transfers.
    """
    return service.list_transfers(
        page=page,
        page_size=page_size,
        product_id=product_id,
        from_warehouse_id=from_warehouse_id,
        to_warehouse_id=to_warehouse_id,
        start_date=start_date,
        end_date=end_date,
        search=search,
    )


@router.post(
    "/stock/recalls",
    response_model=BatchRecallResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_batch_recall(
    payload: BatchRecallCreateRequest,
    service: Annotated[Any, Depends(get_recall_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> BatchRecallResponse:
    """
    Initiate a product batch recall:
    - Flags the batch unsellable immediately (excluded from sales order deductions)
    - Traces all past sales orders and affected buyers that drew from this batch
    """
    return service.initiate_recall(payload=payload, current_user=current_user)


@router.get("/stock/recalls", response_model=BatchRecallListResponse)
def list_batch_recalls(
    service: Annotated[Any, Depends(get_recall_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=200, description="Items per page")] = 50,
    status: Annotated[
        str | None, Query(description="Filter by recall status (initiated, notifying, resolved)")
    ] = None,
    severity: Annotated[
        str | None, Query(description="Filter by severity (low, medium, critical)")
    ] = None,
    product_id: Annotated[str | None, Query(description="Filter by product ID")] = None,
    search: Annotated[str | None, Query(description="Search query")] = None,
) -> BatchRecallListResponse:
    """Fetch paginated, filterable batch recall history."""
    return service.list_recalls(
        page=page,
        page_size=page_size,
        status_filter=status,
        severity_filter=severity,
        product_id=product_id,
        search=search,
    )


@router.get("/stock/recalls/{recall_id}", response_model=BatchRecallResponse)
def get_batch_recall(
    recall_id: str,
    service: Annotated[Any, Depends(get_recall_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> BatchRecallResponse:
    """Retrieve full recall details with all traced affected orders and buyer notification statuses."""
    return service.get_recall_details(recall_id=recall_id)


@router.patch("/stock/recalls/{recall_id}/notify", response_model=BatchRecallNotifyResponse)
def notify_batch_recall(
    recall_id: str,
    service: Annotated[Any, Depends(get_recall_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> BatchRecallNotifyResponse:
    """
    Broadcast recall alerts to all affected retailers via WhatsApp & Email
    and mark affected orders with notified timestamps.
    """
    return service.notify_affected_retailers(recall_id=recall_id, current_user=current_user)


@router.patch("/stock/recalls/{recall_id}/resolve", response_model=BatchRecallResponse)
def resolve_batch_recall(
    recall_id: str,
    service: Annotated[Any, Depends(get_recall_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> BatchRecallResponse:
    """Mark a batch recall as resolved once all affected retailers are confirmed handled."""
    return service.resolve_recall(recall_id=recall_id, current_user=current_user)
