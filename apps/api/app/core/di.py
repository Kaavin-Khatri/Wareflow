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
from app.repositories.impl.alert_log_repository import (
    InMemoryAlertLogRepository,
    SQLAlchemyAlertLogRepository,
)
from app.repositories.impl.audit_repository import SqlAlchemyAuditRepository
from app.repositories.impl.business_settings_repository import (
    InMemoryBusinessSettingsRepository,
    SqlAlchemyBusinessSettingsRepository,
)
from app.repositories.impl.customer_repository import (
    InMemoryCustomerRepository,
    SqlAlchemyCustomerRepository,
)
from app.repositories.impl.inquiry_repository import (
    InMemoryInquiryRepository,
    InquiryRepository as SqlAlchemyInquiryRepository,
)
from app.repositories.impl.invoice_repository import (
    InMemoryInvoiceRepository,
    SqlAlchemyInvoiceRepository,
)
from app.repositories.impl.notification_repository import (
    InMemoryNotificationRepository,
    NotificationRepository as SqlAlchemyNotificationRepository,
)
from app.repositories.impl.payment_repository import (
    InMemoryPaymentRepository,
    SqlAlchemyPaymentRepository,
)
from app.repositories.impl.notification_repository import (
    InMemoryNotificationRepository,
    NotificationRepository,
)
from app.repositories.impl.product_repository import (
    InMemoryProductRepository,
    SqlAlchemyProductRepository,
)
from app.repositories.impl.profile_repository import SqlAlchemyProfileRepository
from app.repositories.impl.purchase_order_repository import (
    InMemoryPurchaseOrderRepository,
    SqlAlchemyPurchaseOrderRepository,
)
from app.repositories.impl.purchase_return_repository import (
    InMemoryPurchaseReturnRepository,
    SqlAlchemyPurchaseReturnRepository,
)
from app.repositories.impl.recall_repository import (
    InMemoryRecallRepository,
    SqlAlchemyRecallRepository,
)
from app.repositories.impl.retailer_repository import (
    InMemoryRetailerRepository,
    SqlAlchemyRetailerRepository,
)
from app.repositories.impl.retailer_user_repository import (
    InMemoryRetailerUserRepository,
    SqlAlchemyRetailerUserRepository,
)
from app.repositories.impl.sales_order_repository import (
    InMemorySalesOrderRepository,
    SqlAlchemySalesOrderRepository,
)
from app.repositories.impl.sales_return_repository import (
    InMemorySalesReturnRepository,
    SqlAlchemySalesReturnRepository,
)
from app.repositories.impl.stock_analytics_repository import (
    SqlAlchemyStockAnalyticsRepository,
)
from app.repositories.impl.stock_repository import (
    SqlAlchemyStockRepository,
)
from app.repositories.impl.supplier_repository import (
    InMemorySupplierRepository,
    SqlAlchemySupplierRepository,
)
from app.repositories.impl.transfer_repository import (
    SqlAlchemyTransferRepository,
)
from app.repositories.impl.uom_repository import (
    SqlAlchemyUomRepository,
)
from app.repositories.interfaces.alert_log_repository import (
    AlertLogRepositoryInterface,
)
from app.repositories.interfaces.audit_repository import AuditRepository
from app.repositories.interfaces.business_settings_repository import (
    BusinessSettingsRepositoryInterface,
)
from app.repositories.interfaces.customer_repository import (
    CustomerRepositoryInterface,
)
from app.repositories.interfaces.inquiry_repository import (
    InquiryRepositoryInterface,
)
from app.repositories.interfaces.invoice_repository import (
    InvoiceRepositoryInterface,
)
from app.repositories.interfaces.notification_repository import (
    NotificationRepositoryInterface,
)
from app.repositories.interfaces.payment_repository import (
    PaymentRepositoryInterface,
)
from app.repositories.interfaces.product_repository import ProductRepositoryInterface
from app.repositories.interfaces.profile_repository import ProfileRepository
from app.repositories.interfaces.purchase_order_repository import (
    PurchaseOrderRepositoryInterface,
)
from app.repositories.interfaces.purchase_return_repository import (
    PurchaseReturnRepositoryInterface,
)
from app.repositories.interfaces.recall_repository import RecallRepositoryInterface
from app.repositories.interfaces.retailer_repository import RetailerRepository
from app.repositories.interfaces.retailer_user_repository import RetailerUserRepository
from app.repositories.interfaces.sales_order_repository import (
    SalesOrderRepositoryInterface,
)
from app.repositories.interfaces.sales_return_repository import (
    SalesReturnRepositoryInterface,
)
from app.repositories.interfaces.stock_analytics_repository import (
    StockAnalyticsRepositoryInterface,
)
from app.repositories.interfaces.stock_repository import StockRepositoryInterface
from app.repositories.interfaces.stock_subscription_repository import (
    StockSubscriptionRepositoryInterface,
)
from app.repositories.interfaces.supplier_repository import SupplierRepositoryInterface
from app.repositories.interfaces.transfer_repository import TransferRepositoryInterface
from app.repositories.interfaces.uom_repository import UomRepositoryInterface
from app.core.alert_scheduler import AlertScheduler
from app.services.alert_engine_service import AlertEngineService
from app.services.audit_service import AuditService
from app.services.business_settings_service import BusinessSettingsService
from app.services.customer_service import CustomerService
from app.services.einvoice_service import EinvoiceService
from app.services.export_service import ExportService
from app.services.inquiry_service import InquiryService
from app.services.invoice_service import InvoiceService
from app.services.ledger_service import LedgerService
from app.services.notification_channels.email_channel import EmailChannel
from app.services.notification_channels.in_app_channel import InAppChannel
from app.services.notification_channels.sms_channel import SmsChannel
from app.services.notification_channels.whatsapp_channel import WhatsAppChannel
from app.services.notification_preference_service import NotificationPreferenceService
from app.services.notification_service import NotificationService
from app.repositories.impl.notification_preference_repository import (
    InMemoryNotificationPreferenceRepository,
    SqlAlchemyNotificationPreferenceRepository,
)
from app.repositories.interfaces.notification_preference_repository import (
    NotificationPreferenceRepositoryInterface,
)
from app.services.payment_service import PaymentService
from app.services.portal_auth_service import PortalAuthService
from app.repositories.impl.delivery_repository import (
    InMemoryDeliveryRepository,
    SqlAlchemyDeliveryRepository,
)
from app.repositories.impl.stock_subscription_repository import (
    InMemoryStockSubscriptionRepository,
    SqlAlchemyStockSubscriptionRepository,
)
from app.repositories.interfaces.delivery_repository import (
    DeliveryRepositoryInterface,
)
from app.services.delivery_service import DeliveryService
from app.services.pricing_strategy import PricingEngineService
from app.services.product_service import ProductService
from app.services.profile_service import ProfileService
from app.services.purchase_order_service import PurchaseOrderService
from app.services.purchase_return_service import PurchaseReturnService
from app.services.recall_service import RecallService
from app.services.retailer_service import RetailerService
from app.services.sales_order_service import SalesOrderService
from app.services.sales_return_service import SalesReturnService
from app.services.staff_service import StaffService
from app.services.stock_analytics_service import StockAnalyticsService
from app.services.stock_service import StockService
from app.services.stock_subscription_service import StockSubscriptionService
from app.services.storage_service import StorageServiceInterface, SupabaseStorageService
from app.repositories.impl.supplier_access_token_repository import (
    InMemorySupplierAccessTokenRepository,
    SqlAlchemySupplierAccessTokenRepository,
)
from app.repositories.interfaces.supplier_access_token_repository import (
    SupplierAccessTokenRepositoryInterface,
)
from app.services.supplier_portal_service import SupplierPortalService
from app.services.supplier_service import SupplierService
from app.services.transfer_service import TransferService
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


@lru_cache
def get_in_memory_retailer_repository() -> RetailerRepository:
    """Factory for in-memory RetailerRepository."""
    return InMemoryRetailerRepository()


def get_retailer_repository(db: Session = Depends(get_db_session)) -> RetailerRepository:
    """Factory for database-backed RetailerRepository interface."""
    return SqlAlchemyRetailerRepository(session=db)


@lru_cache
def get_in_memory_retailer_user_repository() -> RetailerUserRepository:
    """Factory for in-memory RetailerUserRepository."""
    return InMemoryRetailerUserRepository()


def get_retailer_user_repository(db: Session = Depends(get_db_session)) -> RetailerUserRepository:
    """Factory for database-backed RetailerUserRepository interface."""
    return SqlAlchemyRetailerUserRepository(session=db)


@lru_cache
def get_pricing_engine_service() -> PricingEngineService:
    """Factory for PricingEngineService (OCP strategy registry)."""
    return PricingEngineService()


def get_retailer_service(
    repo: RetailerRepository = Depends(get_retailer_repository),
    audit_service: AuditService = Depends(get_audit_service),
    pricing_engine: PricingEngineService = Depends(get_pricing_engine_service),
    retailer_user_repo: RetailerUserRepository = Depends(get_retailer_user_repository),
) -> RetailerService:
    """Factory for RetailerService with audit logging and pluggable pricing."""
    return RetailerService(
        retailer_repo=repo,
        audit_service=audit_service,
        pricing_engine=pricing_engine,
        retailer_user_repo=retailer_user_repo,
    )


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
    audit_repo: AuditRepository = Depends(get_audit_repository),
) -> StockService:
    """Factory for StockService with UoM converter and audit repository."""
    return StockService(stock_repo=stock_repo, uom_repo=uom_repo, audit_repo=audit_repo)


def get_transfer_repository(db: Session = Depends(get_db_session)) -> TransferRepositoryInterface:
    """Factory for database-backed TransferRepositoryInterface."""
    return SqlAlchemyTransferRepository(session=db)


def get_transfer_service(
    transfer_repo: TransferRepositoryInterface = Depends(get_transfer_repository),
    audit_repo: AuditRepository = Depends(get_audit_repository),
) -> TransferService:
    """Factory for TransferService with atomic transfer repository and audit logging."""
    return TransferService(transfer_repo=transfer_repo, audit_repo=audit_repo)


def get_stock_analytics_repository(
    db: Session = Depends(get_db_session),
) -> StockAnalyticsRepositoryInterface:
    """Factory for database-backed StockAnalyticsRepositoryInterface."""
    return SqlAlchemyStockAnalyticsRepository(session=db)


def get_stock_analytics_service(
    repo: StockAnalyticsRepositoryInterface = Depends(get_stock_analytics_repository),
) -> StockAnalyticsService:
    """Factory for StockAnalyticsService."""
    return StockAnalyticsService(analytics_repo=repo)


@lru_cache
def get_supplier_repository() -> SupplierRepositoryInterface:
    """Factory for in-memory SupplierRepositoryInterface."""
    return InMemorySupplierRepository()


def get_db_supplier_repository(
    db: Session = Depends(get_db_session),
) -> SupplierRepositoryInterface:
    """Factory for database-backed SupplierRepositoryInterface."""
    return SqlAlchemySupplierRepository(session=db)


def get_supplier_service(
    repo: SupplierRepositoryInterface = Depends(get_db_supplier_repository),
    audit_service: AuditService = Depends(get_audit_service),
) -> SupplierService:
    """Factory for SupplierService with audit logging."""
    return SupplierService(repository=repo, audit_service=audit_service)


@lru_cache
def get_purchase_order_repository() -> PurchaseOrderRepositoryInterface:
    """Factory for in-memory PurchaseOrderRepositoryInterface."""
    return InMemoryPurchaseOrderRepository()


def get_db_purchase_order_repository(
    db: Session = Depends(get_db_session),
) -> PurchaseOrderRepositoryInterface:
    """Factory for database-backed PurchaseOrderRepositoryInterface."""
    return SqlAlchemyPurchaseOrderRepository(session=db)


@lru_cache
def get_in_memory_supplier_access_token_repository() -> SupplierAccessTokenRepositoryInterface:
    """Factory for in-memory SupplierAccessTokenRepository."""
    return InMemorySupplierAccessTokenRepository()


def get_supplier_access_token_repository(
    db: Session = Depends(get_db_session),
) -> SupplierAccessTokenRepositoryInterface:
    """Factory for database-backed SupplierAccessTokenRepository."""
    return SqlAlchemySupplierAccessTokenRepository(session=db)


@lru_cache
def get_purchase_return_repository() -> PurchaseReturnRepositoryInterface:
    """Factory for in-memory PurchaseReturnRepositoryInterface."""
    return InMemoryPurchaseReturnRepository()


def get_db_purchase_return_repository(
    db: Session = Depends(get_db_session),
) -> PurchaseReturnRepositoryInterface:
    """Factory for database-backed PurchaseReturnRepositoryInterface."""
    return SqlAlchemyPurchaseReturnRepository(session=db)


def get_purchase_return_service(
    return_repo: PurchaseReturnRepositoryInterface = Depends(get_db_purchase_return_repository),
    po_repo: PurchaseOrderRepositoryInterface = Depends(get_db_purchase_order_repository),
    supplier_repo: SupplierRepositoryInterface = Depends(get_db_supplier_repository),
    product_repo: ProductRepositoryInterface = Depends(get_db_product_repository),
    stock_repo: StockRepositoryInterface = Depends(get_stock_repository),
    audit_service: AuditService = Depends(get_audit_service),
) -> PurchaseReturnService:
    """Factory for PurchaseReturnService with DIP dependencies."""
    return PurchaseReturnService(
        purchase_return_repo=return_repo,
        purchase_order_repo=po_repo,
        supplier_repo=supplier_repo,
        product_repo=product_repo,
        stock_repo=stock_repo,
        audit_service=audit_service,
    )


@lru_cache
def get_business_settings_repository() -> BusinessSettingsRepositoryInterface:
    """Factory for in-memory BusinessSettingsRepositoryInterface."""
    return InMemoryBusinessSettingsRepository()


def get_db_business_settings_repository(
    db: Session = Depends(get_db_session),
) -> BusinessSettingsRepositoryInterface:
    """Factory for database-backed BusinessSettingsRepositoryInterface."""
    return SqlAlchemyBusinessSettingsRepository(session=db)


def get_business_settings_service(
    settings_repo: BusinessSettingsRepositoryInterface = Depends(
        get_db_business_settings_repository
    ),
    audit_service: AuditService = Depends(get_audit_service),
) -> BusinessSettingsService:
    """Factory for BusinessSettingsService with DIP dependencies."""
    return BusinessSettingsService(
        repository=settings_repo,
        audit_service=audit_service,
    )


def get_alert_engine_service(
    business_repo: BusinessSettingsRepositoryInterface = Depends(
        get_db_business_settings_repository
    ),
    supplier_repo: SupplierRepositoryInterface = Depends(get_db_supplier_repository),
) -> AlertEngineService:
    """Factory for AlertEngineService registering standard compliance and operational rules."""
    license_rule = ExpiringLicenseRule(
        business_repo=business_repo,
        supplier_repo=supplier_repo,
    )
    engine = AlertEngineService(
        rules=[license_rule],
        business_repo=business_repo,
        supplier_repo=supplier_repo,
    )
    return engine


@lru_cache
def get_sales_order_repository() -> SalesOrderRepositoryInterface:
    """Factory for in-memory SalesOrderRepositoryInterface."""
    return InMemorySalesOrderRepository()


def get_db_sales_order_repository(
    db: Session = Depends(get_db_session),
) -> SalesOrderRepositoryInterface:
    """Factory for database-backed SalesOrderRepositoryInterface."""
    return SqlAlchemySalesOrderRepository(session=db)


@lru_cache
def get_customer_repository() -> CustomerRepositoryInterface:
    """Factory for in-memory CustomerRepositoryInterface."""
    return InMemoryCustomerRepository()


def get_db_customer_repository(
    db: Session = Depends(get_db_session),
) -> CustomerRepositoryInterface:
    """Factory for database-backed CustomerRepositoryInterface."""
    return SqlAlchemyCustomerRepository(session=db)


def get_customer_service(
    customer_repo: CustomerRepositoryInterface = Depends(get_db_customer_repository),
    audit_repo: AuditRepository = Depends(get_audit_repository),
    so_repo: SalesOrderRepositoryInterface = Depends(get_db_sales_order_repository),
) -> CustomerService:
    """Factory for CustomerService with DIP dependencies."""
    return CustomerService(
        customer_repo=customer_repo,
        audit_repo=audit_repo,
        so_repo=so_repo,
    )


def get_sales_order_service(
    so_repo: SalesOrderRepositoryInterface = Depends(get_db_sales_order_repository),
    retailer_repo: RetailerRepository = Depends(get_retailer_repository),
    stock_repo: StockRepositoryInterface = Depends(get_stock_repository),
    product_repo: ProductRepositoryInterface = Depends(get_db_product_repository),
    pricing_engine: PricingEngineService = Depends(get_pricing_engine_service),
    customer_repo: CustomerRepositoryInterface = Depends(get_db_customer_repository),
    uom_service: UomService = Depends(get_uom_service),
    audit_service: AuditService = Depends(get_audit_service),
) -> SalesOrderService:
    """Factory for SalesOrderService with DIP dependencies."""
    return SalesOrderService(
        so_repo=so_repo,
        retailer_repo=retailer_repo,
        stock_repo=stock_repo,
        product_repo=product_repo,
        pricing_engine=pricing_engine,
        customer_repo=customer_repo,
        uom_service=uom_service,
        audit_service=audit_service,
    )


@lru_cache
def get_sales_return_repository() -> SalesReturnRepositoryInterface:
    """Factory for in-memory SalesReturnRepositoryInterface."""
    return InMemorySalesReturnRepository()


def get_db_sales_return_repository(
    db: Session = Depends(get_db_session),
) -> SalesReturnRepositoryInterface:
    """Factory for database-backed SalesReturnRepositoryInterface."""
    return SqlAlchemySalesReturnRepository(session=db)


def get_sales_return_service(
    return_repo: SalesReturnRepositoryInterface = Depends(get_db_sales_return_repository),
    sales_order_repo: SalesOrderRepositoryInterface = Depends(get_db_sales_order_repository),
    stock_repo: StockRepositoryInterface = Depends(get_stock_repository),
    product_repo: ProductRepositoryInterface = Depends(get_db_product_repository),
    audit_service: AuditService = Depends(get_audit_service),
) -> SalesReturnService:
    """Factory for SalesReturnService with DIP dependencies."""
    return SalesReturnService(
        return_repo=return_repo,
        sales_order_repo=sales_order_repo,
        stock_repo=stock_repo,
        product_repo=product_repo,
        audit_service=audit_service,
    )


@lru_cache
def get_recall_repository() -> RecallRepositoryInterface:
    """Factory for in-memory RecallRepositoryInterface."""
    return InMemoryRecallRepository()


def get_db_recall_repository(
    db: Session = Depends(get_db_session),
) -> RecallRepositoryInterface:
    """Factory for database-backed RecallRepositoryInterface."""
    return SqlAlchemyRecallRepository(session=db)


def get_recall_service(
    recall_repo: RecallRepositoryInterface = Depends(get_db_recall_repository),
    stock_repo: StockRepositoryInterface = Depends(get_stock_repository),
    audit_repo: AuditRepository = Depends(get_audit_repository),
) -> RecallService:
    """Factory for RecallService with DIP dependencies."""
    return RecallService(
        recall_repo=recall_repo,
        stock_repo=stock_repo,
        audit_repo=audit_repo,
    )


@lru_cache
def get_invoice_repository() -> InvoiceRepositoryInterface:
    """Factory for in-memory InvoiceRepositoryInterface."""
    return InMemoryInvoiceRepository()


def get_db_invoice_repository(
    db: Session = Depends(get_db_session),
) -> InvoiceRepositoryInterface:
    """Factory for database-backed InvoiceRepositoryInterface."""
    return SqlAlchemyInvoiceRepository(session=db)


@lru_cache
def get_payment_repository() -> PaymentRepositoryInterface:
    """Factory for in-memory PaymentRepositoryInterface."""
    return InMemoryPaymentRepository()


def get_db_payment_repository(
    db: Session = Depends(get_db_session),
) -> PaymentRepositoryInterface:
    """Factory for database-backed PaymentRepositoryInterface."""
    return SqlAlchemyPaymentRepository(session=db)


def get_invoice_service(
    invoice_repo: InvoiceRepositoryInterface = Depends(get_db_invoice_repository),
    sales_order_repo: SalesOrderRepositoryInterface = Depends(get_db_sales_order_repository),
    product_repo: ProductRepositoryInterface = Depends(get_db_product_repository),
    audit_repo: AuditRepository = Depends(get_audit_repository),
    payment_repo: PaymentRepositoryInterface = Depends(get_db_payment_repository),
) -> InvoiceService:
    """Factory for InvoiceService with DIP dependencies."""
    return InvoiceService(
        invoice_repo=invoice_repo,
        sales_order_repo=sales_order_repo,
        product_repo=product_repo,
        audit_repo=audit_repo,
        payment_repo=payment_repo,
    )


def get_payment_service(
    payment_repo: PaymentRepositoryInterface = Depends(get_db_payment_repository),
    invoice_repo: InvoiceRepositoryInterface = Depends(get_db_invoice_repository),
    retailer_repo: RetailerRepository = Depends(get_retailer_repository),
    audit_repo: AuditRepository = Depends(get_audit_repository),
) -> PaymentService:
    """Factory for PaymentService with DIP dependencies."""
    return PaymentService(
        payment_repo=payment_repo,
        invoice_repo=invoice_repo,
        retailer_repo=retailer_repo,
        audit_repo=audit_repo,
    )


def get_ledger_service(
    retailer_repo: RetailerRepository = Depends(get_retailer_repository),
    invoice_repo: InvoiceRepositoryInterface = Depends(get_db_invoice_repository),
    payment_repo: PaymentRepositoryInterface = Depends(get_db_payment_repository),
) -> LedgerService:
    """Factory for LedgerService with DIP dependencies."""
    return LedgerService(
        retailer_repo=retailer_repo,
        invoice_repo=invoice_repo,
        payment_repo=payment_repo,
    )


def get_einvoice_service(
    invoice_repo: InvoiceRepositoryInterface = Depends(get_db_invoice_repository),
    business_repo: BusinessSettingsRepositoryInterface = Depends(get_business_settings_repository),
    audit_repo: AuditRepository = Depends(get_audit_repository),
) -> EinvoiceService:
    """Factory for EinvoiceService with DIP dependencies."""
    return EinvoiceService(
        invoice_repo=invoice_repo,
        business_repo=business_repo,
        audit_repo=audit_repo,
    )


def get_portal_auth_service(
    retailer_user_repo: RetailerUserRepository = Depends(get_retailer_user_repository),
    retailer_repo: RetailerRepository = Depends(get_retailer_repository),
    profile_repo: ProfileRepository = Depends(get_profile_repository),
    order_repo: SalesOrderRepositoryInterface = Depends(get_db_sales_order_repository),
    invoice_repo: InvoiceRepositoryInterface = Depends(get_db_invoice_repository),
    product_repo: ProductRepositoryInterface = Depends(get_db_product_repository),
    stock_repo: StockRepositoryInterface = Depends(get_stock_repository),
    pricing_engine: PricingEngineService = Depends(get_pricing_engine_service),
) -> PortalAuthService:
    """Factory for PortalAuthService with isolated tenant boundaries."""
    return PortalAuthService(
        retailer_user_repo=retailer_user_repo,
        retailer_repo=retailer_repo,
        profile_repo=profile_repo,
        sales_order_repo=order_repo,
        invoice_repo=invoice_repo,
        product_repo=product_repo,
        stock_repo=stock_repo,
        pricing_engine=pricing_engine,
    )


@lru_cache
def get_in_memory_notification_repository() -> NotificationRepositoryInterface:
    """Factory for in-memory NotificationRepository."""
    return InMemoryNotificationRepository()


def get_notification_repository(
    db: Session = Depends(get_db_session),
) -> NotificationRepositoryInterface:
    """Factory for database-backed NotificationRepository."""
    return SqlAlchemyNotificationRepository(session=db)


def get_notification_service(
    notif_repo: NotificationRepositoryInterface = Depends(get_notification_repository),
    retailer_user_repo: RetailerUserRepository = Depends(get_retailer_user_repository),
) -> NotificationService:
    """Factory for NotificationService."""
    return NotificationService(
        notification_repo=notif_repo,
        retailer_user_repo=retailer_user_repo,
    )


@lru_cache
def get_in_memory_inquiry_repository() -> InquiryRepositoryInterface:
    """Factory for in-memory InquiryRepository."""
    return InMemoryInquiryRepository()


def get_inquiry_repository(
    db: Session = Depends(get_db_session),
) -> InquiryRepositoryInterface:
    """Factory for database-backed InquiryRepository."""
    return SqlAlchemyInquiryRepository(session=db)


def get_inquiry_service(
    inquiry_repo: InquiryRepositoryInterface = Depends(get_inquiry_repository),
    product_repo: ProductRepositoryInterface = Depends(get_db_product_repository),
    notif_service: NotificationService = Depends(get_notification_service),
) -> InquiryService:
    """Factory for InquiryService with DIP dependencies."""
    return InquiryService(
        inquiry_repo=inquiry_repo,
        product_repo=product_repo,
        notification_service=notif_service,
    )


@lru_cache
def get_in_memory_delivery_repository() -> DeliveryRepositoryInterface:
    """Factory for in-memory DeliveryRepository."""
    return InMemoryDeliveryRepository()


def get_delivery_repository(
    db: Session = Depends(get_db_session),
) -> DeliveryRepositoryInterface:
    """Factory for database-backed DeliveryRepository."""
    return SqlAlchemyDeliveryRepository(session=db)


def get_delivery_service(
    delivery_repo: DeliveryRepositoryInterface = Depends(get_delivery_repository),
    so_repo: SalesOrderRepositoryInterface = Depends(get_sales_order_repository),
    audit_service: AuditService = Depends(get_audit_service),
    notif_service: NotificationService = Depends(get_notification_service),
) -> DeliveryService:
    """Factory for DeliveryService with DIP dependencies."""
    return DeliveryService(
        delivery_repo=delivery_repo,
        sales_order_repo=so_repo,
        audit_service=audit_service,
        notification_service=notif_service,
    )


def get_export_service(
    so_repo: SalesOrderRepositoryInterface = Depends(get_sales_order_repository),
    business_settings_repo: BusinessSettingsRepositoryInterface = Depends(get_business_settings_repository),
    delivery_repo: DeliveryRepositoryInterface = Depends(get_delivery_repository),
    stock_repo: StockRepositoryInterface = Depends(get_stock_repository),
) -> ExportService:
    """Factory for ExportService with DIP dependencies."""
    return ExportService(
        sales_order_repo=so_repo,
        business_settings_repo=business_settings_repo,
        delivery_repo=delivery_repo,
        stock_repo=stock_repo,
    )


@lru_cache
def get_in_memory_notification_repository() -> NotificationRepositoryInterface:
    """Factory for in-memory NotificationRepository."""
    return InMemoryNotificationRepository()


def get_notification_repository(
    db: Session = Depends(get_db_session),
) -> NotificationRepositoryInterface:
    """Factory for database-backed NotificationRepository."""
    return NotificationRepository(session=db)


def get_notification_service(
    notif_repo: NotificationRepositoryInterface = Depends(get_notification_repository),
    retailer_user_repo: RetailerUserRepository = Depends(get_retailer_user_repository),
) -> NotificationService:
    """Factory for NotificationService with Strategy Pattern channels."""
    settings = get_settings()
    in_app_ch = InAppChannel(notification_repo=notif_repo)
    email_ch = EmailChannel(api_key=settings.resend_api_key)
    whatsapp_ch = WhatsAppChannel(
        access_token=settings.whatsapp_access_token,
        phone_number_id=settings.whatsapp_phone_number_id,
        api_version=settings.whatsapp_api_version,
    )
    sms_ch = SmsChannel(
        account_sid=settings.twilio_account_sid,
        auth_token=settings.twilio_auth_token,
        from_number=settings.twilio_from_number,
        api_key=settings.sms_provider_api_key,
    )
    return NotificationService(
        notification_repo=notif_repo,
        channels=[in_app_ch, email_ch, whatsapp_ch, sms_ch],
        retailer_user_repo=retailer_user_repo,
    )


@lru_cache
def get_in_memory_notification_preference_repository() -> NotificationPreferenceRepositoryInterface:
    """Factory for in-memory NotificationPreferenceRepository."""
    return InMemoryNotificationPreferenceRepository()


def get_notification_preference_repository(
    db: Session = Depends(get_db_session),
) -> NotificationPreferenceRepositoryInterface:
    """Factory for database-backed NotificationPreferenceRepository."""
    return SqlAlchemyNotificationPreferenceRepository(session=db)


def get_notification_preference_service(
    repo: NotificationPreferenceRepositoryInterface = Depends(get_notification_preference_repository),
) -> NotificationPreferenceService:
    """Factory for NotificationPreferenceService."""
    return NotificationPreferenceService(pref_repo=repo)


def get_supplier_portal_service(
    token_repo: SupplierAccessTokenRepositoryInterface = Depends(get_supplier_access_token_repository),
    po_repo: PurchaseOrderRepositoryInterface = Depends(get_db_purchase_order_repository),
    profile_repo: ProfileRepository = Depends(get_profile_repository),
    notif_service: NotificationService = Depends(get_notification_service),
    audit_service: AuditService = Depends(get_audit_service),
) -> SupplierPortalService:
    """Factory for SupplierPortalService with DIP dependencies."""
    return SupplierPortalService(
        token_repo=token_repo,
        po_repo=po_repo,
        profile_repo=profile_repo,
        notification_service=notif_service,
        audit_service=audit_service,
    )


def get_purchase_order_service(
    po_repo: PurchaseOrderRepositoryInterface = Depends(get_db_purchase_order_repository),
    supplier_repo: SupplierRepositoryInterface = Depends(get_db_supplier_repository),
    product_repo: ProductRepositoryInterface = Depends(get_db_product_repository),
    stock_service: StockService = Depends(get_stock_service),
    audit_service: AuditService = Depends(get_audit_service),
    supplier_portal_service: SupplierPortalService = Depends(get_supplier_portal_service),
    token_repo: SupplierAccessTokenRepositoryInterface = Depends(get_supplier_access_token_repository),
) -> PurchaseOrderService:
    """Factory for PurchaseOrderService with DIP dependencies."""
    return PurchaseOrderService(
        po_repo=po_repo,
        supplier_repo=supplier_repo,
        product_repo=product_repo,
        stock_service=stock_service,
        audit_service=audit_service,
        supplier_portal_service=supplier_portal_service,
        token_repo=token_repo,
    )


@lru_cache
def get_in_memory_alert_log_repository() -> AlertLogRepositoryInterface:
    """Factory for in-memory AlertLogRepository."""
    return InMemoryAlertLogRepository()


def get_alert_log_repository(
    db: Session = Depends(get_db_session),
) -> AlertLogRepositoryInterface:
    """Factory for database-backed AlertLogRepository."""
    return SQLAlchemyAlertLogRepository(db=db)


def get_stock_subscription_repository(
    db: Session = Depends(get_db_session),
) -> StockSubscriptionRepositoryInterface:
    """Factory for database-backed StockSubscriptionRepository."""
    return SqlAlchemyStockSubscriptionRepository(session=db)


def get_stock_subscription_service(
    subscription_repo: StockSubscriptionRepositoryInterface = Depends(get_stock_subscription_repository),
    product_repo: ProductRepositoryInterface = Depends(get_db_product_repository),
    retailer_repo: RetailerRepository = Depends(get_retailer_repository),
) -> StockSubscriptionService:
    """Factory for StockSubscriptionService."""
    return StockSubscriptionService(
        subscription_repo=subscription_repo,
        product_repo=product_repo,
        retailer_repo=retailer_repo,
    )


def get_alert_engine_service(
    alert_log_repo: AlertLogRepositoryInterface = Depends(get_alert_log_repository),
    notification_service: NotificationService = Depends(get_notification_service),
    product_repo: ProductRepositoryInterface = Depends(get_db_product_repository),
    stock_repo: StockRepositoryInterface = Depends(get_stock_repository),
    invoice_repo: InvoiceRepositoryInterface = Depends(get_db_invoice_repository),
    profile_repo: ProfileRepository = Depends(get_profile_repository),
    retailer_repo: RetailerRepository = Depends(get_retailer_repository),
    stock_subscription_repo: StockSubscriptionRepositoryInterface = Depends(get_stock_subscription_repository),
    supplier_repo: SupplierRepositoryInterface = Depends(get_db_supplier_repository),
) -> AlertEngineService:
    """Factory for AlertEngineService coordinating rules and deduplication."""
    return AlertEngineService(
        alert_log_repo=alert_log_repo,
        notification_service=notification_service,
        product_repo=product_repo,
        stock_repo=stock_repo,
        invoice_repo=invoice_repo,
        profile_repo=profile_repo,
        retailer_repo=retailer_repo,
        stock_subscription_repo=stock_subscription_repo,
        supplier_repo=supplier_repo,
    )


_global_alert_scheduler: AlertScheduler | None = None


def get_alert_scheduler() -> AlertScheduler:
    """Factory singleton for APScheduler background worker."""
    global _global_alert_scheduler
    if _global_alert_scheduler is None:
        from app.db.session import get_session_factory

        def alert_engine_factory() -> AlertEngineService:
            session_factory = get_session_factory()
            db = session_factory()
            try:
                alert_log_repo = SQLAlchemyAlertLogRepository(db=db)
                notif_repo = NotificationRepository(session=db)
                settings = get_settings()
                notif_service = NotificationService(
                    notification_repo=notif_repo,
                    channels=[
                        InAppChannel(notification_repo=notif_repo),
                        EmailChannel(api_key=settings.resend_api_key),
                        WhatsAppChannel(
                            access_token=settings.whatsapp_access_token,
                            phone_number_id=settings.whatsapp_phone_number_id,
                            api_version=settings.whatsapp_api_version,
                        ),
                    ],
                )
                from app.repositories.impl.product_repository import SqlAlchemyProductRepository
                from app.repositories.impl.stock_repository import SqlAlchemyStockRepository
                from app.repositories.impl.invoice_repository import SqlAlchemyInvoiceRepository
                from app.repositories.impl.profile_repository import SqlAlchemyProfileRepository
                from app.repositories.impl.retailer_repository import SqlAlchemyRetailerRepository
                from app.repositories.impl.stock_subscription_repository import SqlAlchemyStockSubscriptionRepository
                from app.repositories.impl.supplier_repository import SqlAlchemySupplierRepository

                return AlertEngineService(
                    alert_log_repo=alert_log_repo,
                    notification_service=notif_service,
                    product_repo=SqlAlchemyProductRepository(session=db),
                    stock_repo=SqlAlchemyStockRepository(session=db),
                    invoice_repo=SqlAlchemyInvoiceRepository(session=db),
                    profile_repo=SqlAlchemyProfileRepository(session=db),
                    retailer_repo=SqlAlchemyRetailerRepository(session=db),
                    stock_subscription_repo=SqlAlchemyStockSubscriptionRepository(session=db),
                    supplier_repo=SqlAlchemySupplierRepository(session=db),
                )
            finally:
                db.close()

        _global_alert_scheduler = AlertScheduler(
            alert_engine_factory=alert_engine_factory,
            interval_minutes=30,
        )
    return _global_alert_scheduler


