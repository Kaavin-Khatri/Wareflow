"""Product category taxonomy router."""

from fastapi import APIRouter, Depends, status

from app.core.di import get_product_service
from app.core.security import CurrentUser, get_current_user, require_permission
from app.schemas.categories import (
    CategoryCreateRequest,
    CategoryResponse,
    CategoryUpdateRequest,
)
from app.services.product_service import ProductService

router = APIRouter(prefix="/categories", tags=["Product Categories"])


@router.get(
    "",
    response_model=list[CategoryResponse],
    status_code=status.HTTP_200_OK,
    summary="List all categories",
)
def list_categories(
    current_user: CurrentUser = Depends(get_current_user),
    service: ProductService = Depends(get_product_service),
) -> list[CategoryResponse]:
    """Retrieve all product categories."""
    items = service.list_categories()
    return [CategoryResponse.model_validate(c) for c in items]


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get category by ID",
)
def get_category(
    category_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: ProductService = Depends(get_product_service),
) -> CategoryResponse:
    """Retrieve a single category by UUID."""
    category = service.get_category(category_id)
    return CategoryResponse.model_validate(category)


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create category",
)
def create_category(
    payload: CategoryCreateRequest,
    current_user: CurrentUser = Depends(require_permission("inventory:manage")),
    service: ProductService = Depends(get_product_service),
) -> CategoryResponse:
    """Create a new product category."""
    created = service.create_category(payload, actor_id=current_user.id)
    return CategoryResponse.model_validate(created)


@router.patch(
    "/{category_id}",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Update category",
)
def update_category(
    category_id: str,
    payload: CategoryUpdateRequest,
    current_user: CurrentUser = Depends(require_permission("inventory:manage")),
    service: ProductService = Depends(get_product_service),
) -> CategoryResponse:
    """Update category metadata."""
    updated = service.update_category(category_id, payload, actor_id=current_user.id)
    return CategoryResponse.model_validate(updated)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete category",
)
def delete_category(
    category_id: str,
    current_user: CurrentUser = Depends(require_permission("inventory:manage")),
    service: ProductService = Depends(get_product_service),
) -> None:
    """Delete a product category."""
    service.delete_category(category_id, actor_id=current_user.id)
