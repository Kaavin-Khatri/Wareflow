"""Supplier and vendor management router."""

from fastapi import APIRouter, Depends, Query, status

from app.core.di import get_supplier_service
from app.core.security import CurrentUser, get_current_user, require_permission
from app.schemas.suppliers import SupplierCreateRequest, SupplierResponse, SupplierUpdateRequest
from app.services.supplier_service import SupplierService

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


@router.get(
    "",
    response_model=list[SupplierResponse],
    status_code=status.HTTP_200_OK,
    summary="List suppliers",
)
def list_suppliers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    search: str | None = Query(None, description="Search by name, contact, email, or GSTIN"),
    is_active: bool | None = Query(None, description="Filter active/inactive suppliers"),
    current_user: CurrentUser = Depends(get_current_user),
    service: SupplierService = Depends(get_supplier_service),
) -> list[SupplierResponse]:
    """Retrieve goods suppliers with search and active status filters."""
    items = service.list_suppliers(skip=skip, limit=limit, search=search, is_active=is_active)
    return [SupplierResponse.model_validate(s) for s in items]


@router.post(
    "",
    response_model=SupplierResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create supplier",
)
def create_supplier(
    payload: SupplierCreateRequest,
    current_user: CurrentUser = Depends(require_permission("inventory:manage")),
    service: SupplierService = Depends(get_supplier_service),
) -> SupplierResponse:
    """Create a new supplier with duplicate name and GSTIN validation."""
    created = service.create_supplier(payload, actor_id=current_user.id)
    return SupplierResponse.model_validate(created)


@router.get(
    "/{id}",
    response_model=SupplierResponse,
    status_code=status.HTTP_200_OK,
    summary="Get supplier by ID",
)
def get_supplier(
    id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: SupplierService = Depends(get_supplier_service),
) -> SupplierResponse:
    """Retrieve details for a single supplier."""
    supplier = service.get_supplier(id)
    return SupplierResponse.model_validate(supplier)


@router.patch(
    "/{id}",
    response_model=SupplierResponse,
    status_code=status.HTTP_200_OK,
    summary="Update supplier details",
)
def update_supplier(
    id: str,
    payload: SupplierUpdateRequest,
    current_user: CurrentUser = Depends(require_permission("inventory:manage")),
    service: SupplierService = Depends(get_supplier_service),
) -> SupplierResponse:
    """Update metadata, contacts, or active status for an existing supplier."""
    updated = service.update_supplier(id, payload, actor_id=current_user.id)
    return SupplierResponse.model_validate(updated)
