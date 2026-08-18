"""
Dependency injection container and provider factories.

Wires FastAPI Depends() factories to hand services their repository
ABSTRACTIONS (interfaces), never concrete implementation classes directly.

Swapping an implementation here requires modifying zero service code (DIP).
"""

from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db_session
from app.repositories.impl.audit_repository import SqlAlchemyAuditRepository
from app.repositories.impl.product_repository import (
    InMemoryProductRepository,
    SqlAlchemyProductRepository,
)
from app.repositories.impl.profile_repository import SqlAlchemyProfileRepository
from app.repositories.impl.retailer_repository import SqlAlchemyRetailerRepository
from app.repositories.impl.stock_repository import (
    SqlAlchemyStockRepository,
)
from app.repositories.impl.uom_repository import (
    SqlAlchemyUomRepository,
)
from app.repositories.interfaces.audit_repository import AuditRepository
from app.repositories.interfaces.product_repository import ProductRepositoryInterface
from app.repositories.interfaces.profile_repository import ProfileRepository
from app.repositories.interfaces.retailer_repository import RetailerRepository
from app.repositories.interfaces.stock_repository import StockRepositoryInterface
from app.repositories.interfaces.uom_repository import UomRepositoryInterface
from app.services.audit_service import AuditService
from app.services.product_service import ProductService
from app.services.profile_service import ProfileService
from app.services.retailer_service import RetailerService
from app.services.staff_service import StaffService
from app.services.stock_service import StockService
from app.services.storage_service import StorageServiceInterface, SupabaseStorageService
from app.services.two_factor_service import TwoFactorService
from app.services.uom_service import UomService


@lru_cache
def get_product_repository() -> ProductRepositoryInterface:
    """Factory for ProductRepositoryInterface."""
    return InMemoryProductRepository()


def get_db_product_repository(db: Session = Depends(get_db_session)) -> ProductRepositoryInterface:
    """Factory for database-backed ProductRepositoryInterface."""
    return SqlAlchemyProductRepository(session=db)


def get_uom_repository(db: Session = Depends(get_db_session)) -> UomRepositoryInterface:
    """Factory for database-backed UomRepositoryInterface."""
    return SqlAlchemyUomRepository(session=db)


def get_profile_repository(db: Session = Depends(get_db_session)) -> ProfileRepository:
    """Factory for ProfileRepository interface."""
    return SqlAlchemyProfileRepository(session=db)


def get_audit_repository(db: Session = Depends(get_db_session)) -> AuditRepository:
    """Factory for AuditRepository interface."""
    return SqlAlchemyAuditRepository(session=db)


def get_retailer_repository(db: Session = Depends(get_db_session)) -> RetailerRepository:
    """Factory for RetailerRepository interface."""
    return SqlAlchemyRetailerRepository(session=db)


def get_storage_service(
    settings: Settings = Depends(get_settings),
) -> StorageServiceInterface:
    """Factory for StorageServiceInterface using Supabase Storage."""
    return SupabaseStorageService(
        supabase_url=settings.supabase_url,
        service_role_key=settings.supabase_service_role_key,
    )


def get_audit_service(
    audit_repo: AuditRepository = Depends(get_audit_repository),
    profile_repo: ProfileRepository = Depends(get_profile_repository),
) -> AuditService:
    """Factory for AuditService."""
    return AuditService(audit_repo=audit_repo, profile_repo=profile_repo)


def get_uom_service(
    uom_repo: UomRepositoryInterface = Depends(get_uom_repository),
    audit_service: AuditService = Depends(get_audit_service),
) -> UomService:
    """Factory for UomService."""
    return UomService(uom_repo=uom_repo, audit_service=audit_service)


def get_product_service(
    repo: ProductRepositoryInterface = Depends(get_db_product_repository),
    audit_service: AuditService = Depends(get_audit_service),
    storage_service: StorageServiceInterface = Depends(get_storage_service),
) -> ProductService:
    """Factory for ProductService with audit logging and object storage."""
    return ProductService(
        repository=repo,
        audit_service=audit_service,
        storage_service=storage_service,
    )


def get_profile_service(
    repo: ProfileRepository = Depends(get_profile_repository),
) -> ProfileService:
    """Factory for ProfileService."""
    return ProfileService(profile_repo=repo)


def get_staff_service(
    repo: ProfileRepository = Depends(get_profile_repository),
    audit_service: AuditService = Depends(get_audit_service),
) -> StaffService:
    """Factory for StaffService with audit logging."""
    return StaffService(profile_repo=repo, audit_service=audit_service)


def get_retailer_service(
    repo: RetailerRepository = Depends(get_retailer_repository),
    audit_service: AuditService = Depends(get_audit_service),
) -> RetailerService:
    """Factory for RetailerService with audit logging."""
    return RetailerService(retailer_repo=repo, audit_service=audit_service)


def get_two_factor_service(
    repo: ProfileRepository = Depends(get_profile_repository),
) -> TwoFactorService:
    """Factory for TwoFactorService."""
    return TwoFactorService(profile_repo=repo)


def get_stock_repository(db: Session = Depends(get_db_session)) -> StockRepositoryInterface:
    """Factory for database-backed StockRepositoryInterface."""
    return SqlAlchemyStockRepository(session=db)


def get_stock_service(
    stock_repo: StockRepositoryInterface = Depends(get_stock_repository),
    uom_repo: UomRepositoryInterface = Depends(get_uom_repository),
) -> StockService:
    """Factory for StockService with UoM converter."""
    return StockService(stock_repo=stock_repo, uom_repo=uom_repo)
