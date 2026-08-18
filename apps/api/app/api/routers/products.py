"""Product catalog router."""

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from app.core.di import get_product_service
from app.core.security import CurrentUser, get_current_user, require_permission
from app.schemas.products import (
    ProductCreateRequest,
    ProductImageUploadResponse,
    ProductPriceUpdateRequest,
    ProductResponse,
    ProductUpdateRequest,
)
from app.services.product_service import ProductService

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
