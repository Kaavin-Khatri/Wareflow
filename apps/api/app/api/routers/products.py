"""Product catalog router."""

from fastapi import APIRouter, Depends, Query, status

from app.core.di import get_product_service
from app.core.security import CurrentUser, get_current_user, require_permission
from app.schemas.products import ProductPriceUpdateRequest, ProductResponse
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
    current_user: CurrentUser = Depends(get_current_user),
    service: ProductService = Depends(get_product_service),
) -> list[ProductResponse]:
    """Retrieve all catalog products with wholesale pricing."""
    items = service.list_products(skip=skip, limit=limit)
    return [ProductResponse.model_validate(p) for p in items]


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
