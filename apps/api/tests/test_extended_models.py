"""Automated tests for extended wholesale distribution models (Step 2.3)."""

from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.audit_and_settings import AdminAuditLog, BusinessSettings
from app.models.auth_rbac import Permission, Role, RolePermission
from app.models.billing import (
    Invoice,
    InvoiceItem,
    InvoiceStatusEnum,
    Payment,
    PaymentMethodEnum,
)
from app.models.catalog import Product
from app.models.delivery import Delivery, DeliveryStatusEnum
from app.models.portal import (
    ChannelPreferenceEnum,
    Customer,
    InquiryStatusEnum,
    ProductInquiry,
    StockSubscription,
    SupplierAccessToken,
)
from app.models.recalls import (
    BatchRecall,
    RecallAffectedOrder,
    RecallSeverityEnum,
    RecallStatusEnum,
)
from app.models.retailer import BuyerTypeEnum, Retailer, SalesOrder, SOStatusEnum
from app.models.returns import (
    PurchaseReturn,
    PurchaseReturnItem,
    PurchaseReturnStatusEnum,
    ReturnItemConditionEnum,
    SalesReturn,
    SalesReturnItem,
    SalesReturnStatusEnum,
)
from app.models.supplier import PurchaseOrder, Supplier
from app.models.warehouse import StockBatch, Warehouse


@pytest.fixture
def db_session():
    """Create an isolated in-memory SQLite database session for extended model testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def test_invoice_and_payment_credit_netting(db_session: Session):
    """
    Test invoice creation, frozen snapshot items, and payment netting against retailer credit.
    """
    retailer = Retailer(
        name="Mega Hypermarket",
        credit_limit=100000.00,
        credit_balance=25000.00,  # Retailer currently owes 25,000
    )
    product = Product(
        sku="SKU-RICE-25KG",
        name="Basmati Rice 25kg",
        hsn_code="100630",
        wholesale_price=2500.00,
    )
    db_session.add_all([retailer, product])
    db_session.flush()

    so = SalesOrder(
        so_number="SO-202608-100",
        buyer_type=BuyerTypeEnum.RETAILER,
        retailer_id=retailer.id,
        status=SOStatusEnum.DELIVERED,
        total_amount=25000.00,
    )
    db_session.add(so)
    db_session.flush()

    # Create Invoice with frozen snapshot
    invoice = Invoice(
        sales_order_id=so.id,
        invoice_no="INV-202608-100",
        gst_rate=5.00,
        subtotal=23809.52,
        tax_amount=1190.48,
        total_amount=25000.00,
        status=InvoiceStatusEnum.UNPAID,
    )
    item = InvoiceItem(
        invoice=invoice,
        product_id=product.id,
        product_name="Basmati Rice 25kg",  # Frozen name snapshot
        hsn_code="100630",
        qty=10.0,
        unit_price=2380.95,
        tax_rate=5.00,
        tax_amount=1190.48,
        total=25000.00,
    )
    invoice.items.append(item)
    db_session.add(invoice)
    db_session.flush()

    # Retailer makes a partial payment of 10,000 via UPI
    payment = Payment(
        invoice_id=invoice.id,
        retailer_id=retailer.id,
        amount=10000.00,
        method=PaymentMethodEnum.UPI,
        note="UPI Ref 9876543210",
    )
    db_session.add(payment)

    # Net payment against credit balance
    retailer.credit_balance -= payment.amount
    invoice.status = InvoiceStatusEnum.PARTIALLY_PAID
    db_session.commit()

    saved_retailer = db_session.query(Retailer).filter_by(id=retailer.id).first()
    assert saved_retailer is not None
    assert float(saved_retailer.credit_balance) == 15000.00  # 25,000 - 10,000 = 15,000

    saved_invoice = db_session.query(Invoice).filter_by(invoice_no="INV-202608-100").first()
    assert saved_invoice is not None
    assert saved_invoice.status == InvoiceStatusEnum.PARTIALLY_PAID
    assert len(saved_invoice.items) == 1
    assert saved_invoice.items[0].product_name == "Basmati Rice 25kg"


def test_sales_and_purchase_returns(db_session: Session):
    """Test sales returns (with resellable condition) and purchase returns."""
    retailer = Retailer(name="Metro Mart")
    supplier = Supplier(name="Tata Consumer Products")
    warehouse = Warehouse(name="Hub 1")
    product = Product(sku="SKU-TEA-1KG", name="Tata Tea Gold 1kg")
    db_session.add_all([retailer, supplier, warehouse, product])
    db_session.flush()

    batch = StockBatch(
        product_id=product.id,
        warehouse_id=warehouse.id,
        batch_no="B-TEA-001",
        quantity=100.0,
    )
    db_session.add(batch)
    db_session.flush()

    so = SalesOrder(
        so_number="SO-TEA-01",
        retailer_id=retailer.id,
        buyer_type=BuyerTypeEnum.RETAILER,
    )
    po = PurchaseOrder(po_number="PO-TEA-01", supplier_id=supplier.id)
    db_session.add_all([so, po])
    db_session.flush()

    # Sales Return
    sr = SalesReturn(
        sales_order_id=so.id,
        retailer_id=retailer.id,
        status=SalesReturnStatusEnum.APPROVED,
        reason="Overstocked excess units",
    )
    sr_item = SalesReturnItem(
        sales_return=sr,
        product_id=product.id,
        qty=5.0,
        batch_id=batch.id,
        condition=ReturnItemConditionEnum.RESELLABLE,
    )
    sr.items.append(sr_item)
    db_session.add(sr)

    # Purchase Return
    pr = PurchaseReturn(
        purchase_order_id=po.id,
        supplier_id=supplier.id,
        status=PurchaseReturnStatusEnum.REQUESTED,
        reason="Damaged in transit from factory",
    )
    pr_item = PurchaseReturnItem(
        purchase_return=pr,
        product_id=product.id,
        qty=2.0,
        batch_id=batch.id,
        reason="Outer box crushed",
    )
    pr.items.append(pr_item)
    db_session.add(pr)
    db_session.commit()

    saved_sr = db_session.query(SalesReturn).first()
    assert saved_sr is not None
    assert saved_sr.status == SalesReturnStatusEnum.APPROVED
    assert saved_sr.items[0].condition == ReturnItemConditionEnum.RESELLABLE

    saved_pr = db_session.query(PurchaseReturn).first()
    assert saved_pr is not None
    assert saved_pr.status == PurchaseReturnStatusEnum.REQUESTED


def test_delivery_and_rbac_permissions(db_session: Session):
    """Test delivery dispatch and RBAC role permission mappings."""
    retailer = Retailer(name="Shivaji Stores")
    db_session.add(retailer)
    db_session.flush()

    so = SalesOrder(
        so_number="SO-DEL-01",
        retailer_id=retailer.id,
        buyer_type=BuyerTypeEnum.RETAILER,
    )
    db_session.add(so)
    db_session.flush()

    delivery = Delivery(
        sales_order_id=so.id,
        driver_name="Sanjay Shinde",
        vehicle_no="MH-04-AB-1234",
        status=DeliveryStatusEnum.OUT_FOR_DELIVERY,
        dispatched_at=datetime.now(),
    )
    db_session.add(delivery)

    # RBAC Setup
    admin_role = Role(name="admin", description="Full administrator access")
    inv_perm = Permission(code="inventory:manage", description="Manage stock and warehouses")
    db_session.add_all([admin_role, inv_perm])
    db_session.flush()

    rp = RolePermission(role_id=admin_role.id, permission_id=inv_perm.id)
    db_session.add(rp)
    db_session.commit()

    saved_delivery = db_session.query(Delivery).first()
    assert saved_delivery is not None
    assert saved_delivery.status == DeliveryStatusEnum.OUT_FOR_DELIVERY
    assert saved_delivery.driver_name == "Sanjay Shinde"

    saved_role = db_session.query(Role).filter_by(name="admin").first()
    assert saved_role is not None
    assert len(saved_role.permissions) == 1
    assert saved_role.permissions[0].permission.code == "inventory:manage"


def test_portal_customer_magic_link_and_audit(db_session: Session):
    """Test walk-in customer order, magic link access token, recall, and audit log."""
    customer = Customer(
        name="Anil Sharma",
        phone="+919876500000",
        email="anil@gmail.com",
    )
    product = Product(sku="SKU-SOAP-100G", name="Sandal Soap 100g")
    supplier = Supplier(name="Godrej Consumer")
    warehouse = Warehouse(name="Hub 2")
    db_session.add_all([customer, product, supplier, warehouse])
    db_session.flush()

    batch = StockBatch(
        product_id=product.id,
        warehouse_id=warehouse.id,
        batch_no="B-SOAP-99",
        quantity=200.0,
    )
    po = PurchaseOrder(po_number="PO-MAGIC-01", supplier_id=supplier.id)
    db_session.add_all([batch, po])
    db_session.flush()

    # 1. Walk-in Customer Sales Order
    so = SalesOrder(
        so_number="SO-CUST-001",
        buyer_type=BuyerTypeEnum.CUSTOMER,
        customer_id=customer.id,
        total_amount=500.00,
    )
    db_session.add(so)
    db_session.flush()

    # 2. Supplier Magic Link Token
    magic_token = SupplierAccessToken(
        supplier_id=supplier.id,
        purchase_order_id=po.id,
        token="tok_magic_secure_hash_123",
        expires_at=datetime.now() + timedelta(days=7),
    )
    db_session.add(magic_token)

    # 3. Stock Subscription
    sub = StockSubscription(
        retailer_id=supplier.id,  # using ID for relation check
        product_id=product.id,
        channel_preference=ChannelPreferenceEnum.WHATSAPP,
    )
    # 4. Product Inquiry
    inquiry = ProductInquiry(
        product_id=product.id,
        customer_id=customer.id,
        message="Can I get 50 boxes delivered tomorrow?",
        status=InquiryStatusEnum.OPEN,
    )
    db_session.add_all([sub, inquiry])

    # 5. Batch Recall
    recall = BatchRecall(
        batch_id=batch.id,
        product_id=product.id,
        reason="Packaging seal integrity defect",
        severity=RecallSeverityEnum.CRITICAL,
        status=RecallStatusEnum.INITIATED,
    )
    affected = RecallAffectedOrder(
        recall=recall,
        sales_order_id=so.id,
        customer_id=customer.id,
    )
    recall.affected_orders.append(affected)
    db_session.add(recall)

    # 6. Admin Audit Log
    audit = AdminAuditLog(
        actor_id="admin_user_1",
        action="UPDATE_CREDIT_LIMIT",
        entity_type="retailer",
        entity_id="ret_123",
        before_value={"credit_limit": 50000},
        after_value={"credit_limit": 100000},
    )
    # 7. Business Settings
    biz = BusinessSettings(
        business_name="Khatri Wholesale Traders",
        gstin="27AAACK1234F1Z1",
        fssai_license_no="11518018000456",
        fssai_expiry_date=date(2028, 10, 15),
        address="APMC Market, Vashi, Navi Mumbai 400703",
        phone="+919820012345",
        email="contact@khatriwholesale.com",
    )
    db_session.add_all([audit, biz])
    db_session.commit()

    saved_so = db_session.query(SalesOrder).filter_by(so_number="SO-CUST-001").first()
    assert saved_so is not None
    assert saved_so.buyer_type == BuyerTypeEnum.CUSTOMER
    assert saved_so.customer.name == "Anil Sharma"

    saved_token = (
        db_session.query(SupplierAccessToken).filter_by(token="tok_magic_secure_hash_123").first()
    )
    assert saved_token is not None
    assert saved_token.supplier.name == "Godrej Consumer"

    saved_biz = db_session.query(BusinessSettings).first()
    assert saved_biz is not None
    assert saved_biz.business_name == "Khatri Wholesale Traders"
