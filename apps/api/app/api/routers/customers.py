"""Direct Walk-In and Retail End-Customer router."""

from fastapi import APIRouter, Depends, Query, status

from app.core.di import get_customer_service
from app.core.security import CurrentUser, get_current_user
from app.schemas.customers import (
    CustomerCreateRequest,
    CustomerResponse,
    CustomerUpdateRequest,
)
from app.services.customer_service import CustomerService

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get(
    "",
    response_model=list[CustomerResponse],
    status_code=status.HTTP_200_OK,
    summary="List direct walk-in customers",
)
def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    search: str | None = Query(
        None, description="Search query by name, phone, email, or notes"
    ),
    current_user: CurrentUser = Depends(get_current_user),
    service: CustomerService = Depends(get_customer_service),
) -> list[CustomerResponse]:
    """Retrieve direct/walk-in customer accounts with optional search query."""
    res = service.list_customers(skip=skip, limit=limit, search=search)
    return res.items


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a direct customer",
)
def create_customer(
    payload: CustomerCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: CustomerService = Depends(get_customer_service),
) -> CustomerResponse:
    """Register a new direct end-customer for walk-in or one-off sales."""
    return service.create_customer(payload=payload, current_user=current_user)


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
    status_code=status.HTTP_200_OK,
    summary="Get direct customer details by ID",
)
def get_customer(
    customer_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: CustomerService = Depends(get_customer_service),
) -> CustomerResponse:
    """Retrieve customer details along with order metrics."""
    return service.get_customer(customer_id)


@router.patch(
    "/{customer_id}",
    response_model=CustomerResponse,
    status_code=status.HTTP_200_OK,
    summary="Update direct customer profile",
)
def update_customer(
    customer_id: str,
    payload: CustomerUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: CustomerService = Depends(get_customer_service),
) -> CustomerResponse:
    """Update contact information or internal notes for a direct customer."""
    return service.update_customer(customer_id=customer_id, payload=payload, current_user=current_user)


@router.delete(
    "/{customer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete direct customer profile",
)
def delete_customer(
    customer_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: CustomerService = Depends(get_customer_service),
) -> None:
    """Delete a customer profile if no associated sales orders exist."""
    service.delete_customer(customer_id=customer_id, current_user=current_user)
