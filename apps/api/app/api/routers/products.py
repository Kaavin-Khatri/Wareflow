"""Product catalog router."""

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
    status,
)

from app.core.di import (
    get_forecasting_service,
    get_product_import_service,
    get_product_service,
    get_stock_subscription_service,
)
from app.core.limiter import limiter
from app.core.security import CurrentUser, get_current_user, require_permission
from app.schemas.forecast import ProductForecastResponse
from app.schemas.imports import ProductImportResponse
from app.schemas.products import (
    ProductCreateRequest,
    ProductImageUploadResponse,
    ProductPriceUpdateRequest,
    ProductResponse,
    ProductUpdateRequest,
)
from app.schemas.stock_subscriptions import (
    RetailerSubscribeRequest,
    StockSubscriptionResponse,
)
from app.services.forecasting_service import ForecastingService
from app.services.import_service import ProductImportService
from app.services.product_service import ProductService
from app.services.stock_subscription_service import StockSubscriptionService

router = APIRouter(prefix="/products", tags=["Product Catalog"])


@router.get(
    "",
    response_model=list[ProductResponse],
    status_code=status.HTTP_200_OK,
    summary="List wholesale products",
)
def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    category_id: str | None = Query(None, description="Filter by category UUID"),
    search: str | None = Query(None, description="Search by name, SKU, barcode, or HSN"),
    is_active: bool | None = Query(None, description="Filter active/inactive products"),
    current_user: CurrentUser = Depends(get_current_user),
    service: ProductService = Depends(get_product_service),
) -> list[ProductResponse]:
    """Retrieve catalog products with pricing, filtering, and search."""
    items = service.list_products(
        skip=skip,
        limit=limit,
        category_id=category_id,
        search=search,
        is_active=is_active,
    )
    return [ProductResponse.model_validate(p) for p in items]


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create product",
)
def create_product(
    payload: ProductCreateRequest,
    current_user: CurrentUser = Depends(require_permission("inventory:manage")),
    service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    """Create a new wholesale product record."""
    created = service.create_product(payload, actor_id=current_user.id)
    return ProductResponse.model_validate(created)


@router.post(
    "/import",
    response_model=ProductImportResponse,
    status_code=status.HTTP_200_OK,
    summary="Bulk CSV product import with dry-run preview and upsert",
)
@limiter.limit("10/minute")
async def import_products_csv(
    request: Request,
    file: UploadFile = File(...),
    dry_run: bool = Query(True, description="When True, validates and previews without committing to DB"),
    current_user: CurrentUser = Depends(require_permission("inventory:manage")),
    import_service: ProductImportService = Depends(get_product_import_service),
) -> ProductImportResponse:
    """Upload CSV to preview or commit bulk catalog products with safe upsert-by-SKU."""
    if not file.filename or not (
        file.filename.lower().endswith(".csv")
        or file.content_type in ("text/csv", "application/vnd.ms-excel", "text/plain", "application/octet-stream")
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a valid CSV document.",
        )

    content_bytes = await file.read()
    if not content_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded CSV file is empty.",
        )

    if dry_run:
        return import_service.preview_import(content_bytes)
    else:
        return import_service.execute_import(content_bytes, actor_id=current_user.id)


@router.get(
    "/export.csv",
    response_class=Response,
    status_code=status.HTTP_200_OK,
    summary="Export all catalog products to CSV",
    responses={200: {"content": {"text/csv": {}}}},
)
def export_products_csv(
    current_user: CurrentUser = Depends(get_current_user),
    import_service: ProductImportService = Depends(get_product_import_service),
) -> Response:
    """Download full wholesale catalog as a CSV spreadsheet."""
    csv_str = import_service.export_catalog_csv()
    return Response(
        content=csv_str.encode("utf-8-sig"),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="wareflow_products_catalog.csv"'},
    )


@router.get(
    "/template.csv",
    response_class=Response,
    status_code=status.HTTP_200_OK,
    summary="Download sample CSV template for product import",
    responses={200: {"content": {"text/csv": {}}}},
)
def download_import_template_csv(
    current_user: CurrentUser = Depends(get_current_user),
    import_service: ProductImportService = Depends(get_product_import_service),
) -> Response:
    """Download standard sample CSV template with expected headers and sample FMCG products."""
    template_str = import_service.generate_csv_template()
    return Response(
        content=template_str.encode("utf-8"),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="wareflow_product_import_template.csv"'},
    )


@router.get(
    "/by-barcode/{barcode}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Resolve product by barcode or SKU",
)
def get_product_by_barcode(
    barcode: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    """Instantly lookup and return a product by its barcode or scanned code."""
    product = service.get_product_by_barcode(barcode)
    return ProductResponse.model_validate(product)


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Get product by ID",
)
def get_product(
    product_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    """Retrieve product details by UUID."""
    product = service.get_product(product_id)
    return ProductResponse.model_validate(product)


@router.get(
    "/{product_id}/barcode.png",
    response_class=Response,
    status_code=status.HTTP_200_OK,
    summary="Generate and render product barcode as PNG image",
    responses={200: {"content": {"image/png": {}}}},
)
def get_product_barcode_png(
    product_id: str,
    service: ProductService = Depends(get_product_service),
) -> Response:
    """Render high-resolution scannable barcode PNG image for printing, labels, and mobile display."""
    png_bytes = service.get_product_barcode_image(product_id)
    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={"Content-Disposition": f'inline; filename="product_{product_id}_barcode.png"'},
    )


@router.get(
    "/{product_id}/qr.png",
    response_class=Response,
    status_code=status.HTTP_200_OK,
    summary="Generate and render product QR code as PNG image",
    responses={200: {"content": {"image/png": {}}}},
)
def get_product_qr_png(
    product_id: str,
    service: ProductService = Depends(get_product_service),
) -> Response:
    """Render 2D QR code PNG image for fast camera scanning and label sheets."""
    png_bytes = service.get_product_qr_image(product_id)
    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={"Content-Disposition": f'inline; filename="product_{product_id}_qr.png"'},
    )


@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Update product details",
)
def update_product(
    product_id: str,
    payload: ProductUpdateRequest,
    current_user: CurrentUser = Depends(require_permission("inventory:manage")),
    service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    """Update metadata, pricing, or status on an existing product."""
    updated = service.update_product(product_id, payload, actor_id=current_user.id)
    return ProductResponse.model_validate(updated)


@router.patch(
    "/{product_id}/price",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Update product selling/cost price",
)
def update_product_price(
    product_id: str,
    payload: ProductPriceUpdateRequest,
    current_user: CurrentUser = Depends(require_permission("inventory:manage")),
    service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    """Update wholesale price or cost price of a product and log the change."""
    updated = service.update_price(
        product_id=product_id,
        wholesale_price=payload.wholesale_price,
        cost_price=payload.cost_price,
        actor_id=current_user.id,
    )
    return ProductResponse.model_validate(updated)


@router.post(
    "/{product_id}/deactivate",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Deactivate product",
)
def deactivate_product(
    product_id: str,
    current_user: CurrentUser = Depends(require_permission("inventory:manage")),
    service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    """Deactivate a product (blocked if open POs or SOs exist)."""
    deactivated = service.deactivate_product(product_id, actor_id=current_user.id)
    return ProductResponse.model_validate(deactivated)


@router.post(
    "/{product_id}/image",
    response_model=ProductImageUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload product image",
)
async def upload_product_image(
    product_id: str,
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(require_permission("inventory:manage")),
    service: ProductService = Depends(get_product_service),
) -> ProductImageUploadResponse:
    """Upload product image file (JPEG/PNG/WebP, <=5MB) and persist public URL."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename cannot be empty.",
        )

    file_bytes = await file.read()
    content_type = file.content_type or "image/jpeg"

    image_url = service.upload_image(
        product_id=product_id,
        file_bytes=file_bytes,
        filename=file.filename,
        content_type=content_type,
        actor_id=current_user.id,
    )

    return ProductImageUploadResponse(product_id=product_id, image_url=image_url)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete product",
)
def delete_product(
    product_id: str,
    current_user: CurrentUser = Depends(require_permission("inventory:manage")),
    service: ProductService = Depends(get_product_service),
) -> None:
    """Permanently delete a product record."""
    service.delete_product(product_id, actor_id=current_user.id)


@router.post(
    "/{product_id}/subscribe",
    response_model=StockSubscriptionResponse,
    status_code=status.HTTP_200_OK,
    summary="Subscribe retailer to product restock alerts",
)
def subscribe_retailer_to_product(
    product_id: str,
    payload: RetailerSubscribeRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: StockSubscriptionService = Depends(get_stock_subscription_service),
) -> StockSubscriptionResponse:
    """Subscribe or reactivate a retailer's standing back-in-stock alert subscription."""
    return service.subscribe(
        product_id=product_id,
        retailer_id=payload.retailer_id,
        channel_preference=payload.channel_preference,
    )


@router.delete(
    "/{product_id}/subscribe",
    status_code=status.HTTP_200_OK,
    summary="Unsubscribe retailer from product restock alerts",
)
def unsubscribe_retailer_from_product(
    product_id: str,
    retailer_id: str = Query(..., description="Retailer UUID to unsubscribe"),
    current_user: CurrentUser = Depends(get_current_user),
    service: StockSubscriptionService = Depends(get_stock_subscription_service),
) -> dict[str, bool]:
    """Unsubscribe a retailer by deactivating their standing subscription."""
    service.unsubscribe(product_id=product_id, retailer_id=retailer_id)
    return {"success": True}


@router.get(
    "/{product_id}/subscribers",
    response_model=list[StockSubscriptionResponse],
    status_code=status.HTTP_200_OK,
    summary="List active restock subscribers for a product",
)
def list_product_subscribers(
    product_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: StockSubscriptionService = Depends(get_stock_subscription_service),
) -> list[StockSubscriptionResponse]:
    """Staff-visible list of active restock subscribers for demand insight."""
    return service.list_subscribers_for_product(product_id=product_id)


@router.get(
    "/{id}/forecast",
    response_model=ProductForecastResponse,
    status_code=status.HTTP_200_OK,
    summary="Get statistical demand forecast for a product",
)
def get_product_demand_forecast(
    id: str,
    horizon_days: int = Query(30, ge=1, le=365, description="Prediction horizon in days"),
    strategy: str | None = Query(
        None, description="Forecasting strategy override ('moving_average', 'exponential_smoothing')"
    ),
    force_refresh: bool = Query(False, description="Bypass 24h cache and recompute immediately"),
    current_user: CurrentUser = Depends(get_current_user),
    service: ForecastingService = Depends(get_forecasting_service),
) -> ProductForecastResponse:
    """Predict demand for the product based on movement history using pluggable strategy with 24h cache."""
    return service.get_product_forecast(
        product_id=id,
        horizon_days=horizon_days,
        strategy_name=strategy,
        force_refresh=force_refresh,
    )

