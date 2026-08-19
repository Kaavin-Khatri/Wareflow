"""SQLAlchemy ORM models package."""

from app.models.audit_and_settings import AdminAuditLog, BusinessSettings
from app.models.auth_rbac import Permission, Role, RolePermission
from app.models.billing import Invoice, InvoiceItem, InvoiceStatusEnum, Payment, PaymentMethodEnum
from app.models.catalog import Category, Product
from app.models.delivery import Delivery, DeliveryStatusEnum
from app.models.forecast import Forecast
from app.models.inventory import StockMovement, StockMovementTypeEnum
from app.models.notification import AlertLog, Notification, NotificationPreference
from app.models.portal import (
    ChannelPreferenceEnum,
    Customer,
    InquiryStatusEnum,
    ProductInquiry,
    RetailerPortalInvite,
    RetailerUser,
    StockSubscription,
    SupplierAccessToken,
)
from app.models.profile import Profile
from app.models.recalls import (
    BatchRecall,
    RecallAffectedOrder,
    RecallSeverityEnum,
    RecallStatusEnum,
)
from app.models.retailer import BuyerTypeEnum, Retailer, SalesOrder, SalesOrderItem, SOStatusEnum
from app.models.returns import (
    PurchaseReturn,
    PurchaseReturnItem,
    PurchaseReturnStatusEnum,
    ReturnItemConditionEnum,
    SalesReturn,
    SalesReturnItem,
    SalesReturnStatusEnum,
)
from app.models.supplier import POStatusEnum, PurchaseOrder, PurchaseOrderItem, Supplier
from app.models.uom import ProductUOMConversion, UnitOfMeasure
from app.models.warehouse import StockBatch, Warehouse

__all__ = [
    # Auth & Profiles
    "Profile",
    # Catalog & UOM
    "Category",
    "Product",
    "UnitOfMeasure",
    "ProductUOMConversion",
    # Warehouse & Batches
    "Warehouse",
    "StockBatch",
    # Suppliers & Procurement
    "Supplier",
    "PurchaseOrder",
    "PurchaseOrderItem",
    "POStatusEnum",
    # Retailers, Customers & Sales Orders
    "Retailer",
    "Customer",
    "SalesOrder",
    "SalesOrderItem",
    "SOStatusEnum",
    "BuyerTypeEnum",
    # Invoicing & Payments
    "Invoice",
    "InvoiceItem",
    "InvoiceStatusEnum",
    "Payment",
    "PaymentMethodEnum",
    # Returns
    "SalesReturn",
    "SalesReturnItem",
    "SalesReturnStatusEnum",
    "ReturnItemConditionEnum",
    "PurchaseReturn",
    "PurchaseReturnItem",
    "PurchaseReturnStatusEnum",
    # Delivery
    "Delivery",
    "DeliveryStatusEnum",
    # RBAC
    "Role",
    "Permission",
    "RolePermission",
    # Portal & Subscriptions
    "RetailerUser",
    "RetailerPortalInvite",
    "StockSubscription",
    "SupplierAccessToken",
    "ProductInquiry",
    "ChannelPreferenceEnum",
    "InquiryStatusEnum",
    # Recalls
    "BatchRecall",
    "RecallAffectedOrder",
    "RecallSeverityEnum",
    "RecallStatusEnum",
    # Inventory & Alerts
    "StockMovement",
    "StockMovementTypeEnum",
    "Notification",
    "AlertLog",
    "NotificationPreference",
    "Forecast",
    # Audit & Business Settings
    "AdminAuditLog",
    "BusinessSettings",
]
