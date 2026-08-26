"""FastAPI endpoints for Units of Measure and Product Conversions."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.di import get_uom_service
from app.core.security import CurrentUser, get_current_user, require_permission
from app.schemas.uom import (
    ProductUOMConversionCreateRequest,
    ProductUOMConversionResponse,
    UOMConvertRequest,
    UOMConvertResponse,
    UOMCreateRequest,
    UOMResponse,
    UOMUpdateRequest,
)
from app.services.uom_service import UomConversionError, UomService

router = APIRouter(tags=["Units of Measure"])


@router.get("/uom", response_model=list[UOMResponse])
def list_uoms(
    service: Annotated[UomService, Depends(get_uom_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> list[UOMResponse]:
    """List all units of measure."""
    return service.list_uoms()  # type: ignore[return-value]


@router.get("/uom/{uom_id}", response_model=UOMResponse)
def get_uom_by_id(
    uom_id: str,
    service: Annotated[UomService, Depends(get_uom_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> UOMResponse:
    """Get unit of measure details by ID."""
    return service.get_uom(uom_id)  # type: ignore[return-value]


@router.post("/uom", response_model=UOMResponse, status_code=status.HTTP_201_CREATED)
def create_uom(
    payload: UOMCreateRequest,
    service: Annotated[UomService, Depends(get_uom_service)],
    current_user: Annotated[CurrentUser, Depends(require_permission("inventory:manage"))],
) -> UOMResponse:
    """Create a new unit of measure."""
    return service.create_uom(  # type: ignore[return-value]
        name=payload.name,
        abbreviation=payload.abbreviation,
        actor_id=current_user.id,
    )


@router.patch("/uom/{uom_id}", response_model=UOMResponse)
def update_uom(
    uom_id: str,
    payload: UOMUpdateRequest,
    service: Annotated[UomService, Depends(get_uom_service)],
    current_user: Annotated[CurrentUser, Depends(require_permission("inventory:manage"))],
) -> UOMResponse:
    """Update an existing unit of measure."""
    return service.update_uom(  # type: ignore[return-value]
        uom_id=uom_id,
        name=payload.name,
        abbreviation=payload.abbreviation,
        actor_id=current_user.id,
    )


@router.delete("/uom/{uom_id}")
def delete_uom(
    uom_id: str,
    service: Annotated[UomService, Depends(get_uom_service)],
    current_user: Annotated[CurrentUser, Depends(require_permission("inventory:manage"))],
) -> dict[str, bool]:
    """Delete a unit of measure."""
    deleted = service.delete_uom(uom_id=uom_id, actor_id=current_user.id)
    return {"deleted": deleted}


@router.get("/products/{product_id}/conversions", response_model=list[ProductUOMConversionResponse])
def list_product_conversions(
    product_id: str,
    service: Annotated[UomService, Depends(get_uom_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> list[ProductUOMConversionResponse]:
    """List all packaging conversion ratios defined for a product."""
    return service.list_product_conversions(product_id)  # type: ignore[return-value]


@router.post(
    "/products/{product_id}/conversions",
    response_model=ProductUOMConversionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_or_update_conversion(
    product_id: str,
    payload: ProductUOMConversionCreateRequest,
    service: Annotated[UomService, Depends(get_uom_service)],
    current_user: Annotated[CurrentUser, Depends(require_permission("inventory:manage"))],
) -> ProductUOMConversionResponse:
    """Define or update a packaging conversion ratio for a product."""
    return service.create_or_update_conversion(  # type: ignore[return-value]
        product_id=product_id,
        from_uom_id=payload.from_uom_id,
        to_uom_id=payload.to_uom_id,
        factor=payload.factor,
        actor_id=current_user.id,
    )


@router.delete("/products/{product_id}/conversions/{conversion_id}")
def delete_product_conversion(
    product_id: str,
    conversion_id: str,
    service: Annotated[UomService, Depends(get_uom_service)],
    current_user: Annotated[CurrentUser, Depends(require_permission("inventory:manage"))],
) -> dict[str, bool]:
    """Delete a packaging conversion ratio for a product."""
    deleted = service.delete_conversion(
        conversion_id=conversion_id,
        actor_id=current_user.id,
    )
    return {"deleted": deleted}


@router.post("/products/{product_id}/convert", response_model=UOMConvertResponse)
def calculate_conversion(
    product_id: str,
    payload: UOMConvertRequest,
    service: Annotated[UomService, Depends(get_uom_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> UOMConvertResponse:
    """Calculate conversion between two UoMs for a product."""
    try:
        converted_qty = service.convert(
            product_id=product_id,
            qty=payload.qty,
            from_uom_id=payload.from_uom_id,
            to_uom_id=payload.to_uom_id,
        )
        return UOMConvertResponse(
            product_id=product_id,
            original_qty=payload.qty,
            from_uom_id=payload.from_uom_id,
            to_uom_id=payload.to_uom_id,
            converted_qty=converted_qty,
        )
    except UomConversionError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err
