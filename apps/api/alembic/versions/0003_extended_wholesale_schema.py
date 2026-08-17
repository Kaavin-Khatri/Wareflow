"""extended wholesale schema

Revision ID: 0003_extended_wholesale_schema
Revises: 0002_core_wholesale_schema
Create Date: 2026-08-17 18:20:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003_extended_wholesale_schema"
down_revision: str | Sequence[str] | None = "0002_core_wholesale_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Customers (Walk-in / Direct Buyers)
    op.create_table(
        "customers",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("email", sa.String(length=100), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # 2. Update Sales Orders with Buyer Type and Customer ID
    op.add_column(
        "sales_orders",
        sa.Column("buyer_type", sa.String(length=50), nullable=False, server_default="retailer"),
    )
    op.add_column(
        "sales_orders",
        sa.Column(
            "customer_id",
            sa.String(length=36),
            sa.ForeignKey("customers.id", ondelete="RESTRICT"),
            nullable=True,
        ),
    )
    op.alter_column("sales_orders", "retailer_id", nullable=True)
    op.create_index("ix_sales_orders_retailer_id", "sales_orders", ["retailer_id"])
    op.create_index("ix_sales_orders_customer_id", "sales_orders", ["customer_id"])

    # 3. Invoices
    op.create_table(
        "invoices",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "sales_order_id",
            sa.String(length=36),
            sa.ForeignKey("sales_orders.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("invoice_no", sa.String(length=50), nullable=False, unique=True),
        sa.Column(
            "invoice_date",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "gst_rate",
            sa.Numeric(precision=5, scale=2),
            nullable=False,
            server_default="18.00",
        ),
        sa.Column(
            "subtotal",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column(
            "tax_amount",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column(
            "total_amount",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="unpaid"),
        sa.Column("e_invoice_irn", sa.String(length=100), nullable=True),
        sa.Column("e_invoice_ack_no", sa.String(length=50), nullable=True),
        sa.Column("e_invoice_qr_code", sa.Text(), nullable=True),
        sa.Column("e_way_bill_no", sa.String(length=50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_invoices_invoice_no", "invoices", ["invoice_no"])
    op.create_index("ix_invoices_sales_order_id", "invoices", ["sales_order_id"])

    # 4. Invoice Items (Frozen Accounting Snapshot)
    op.create_table(
        "invoice_items",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "invoice_id",
            sa.String(length=36),
            sa.ForeignKey("invoices.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            sa.String(length=36),
            sa.ForeignKey("products.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("product_name", sa.String(length=255), nullable=False),
        sa.Column("hsn_code", sa.String(length=50), nullable=True),
        sa.Column("qty", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("unit_price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column(
            "tax_rate",
            sa.Numeric(precision=5, scale=2),
            nullable=False,
            server_default="18.00",
        ),
        sa.Column(
            "tax_amount",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column(
            "total",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column(
            "uom_id",
            sa.String(length=36),
            sa.ForeignKey("units_of_measure.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_invoice_items_invoice_id", "invoice_items", ["invoice_id"])
    op.create_index("ix_invoice_items_product_id", "invoice_items", ["product_id"])

    # 5. Payments
    op.create_table(
        "payments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "invoice_id",
            sa.String(length=36),
            sa.ForeignKey("invoices.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "retailer_id",
            sa.String(length=36),
            sa.ForeignKey("retailers.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "customer_id",
            sa.String(length=36),
            sa.ForeignKey("customers.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("method", sa.String(length=50), nullable=False),
        sa.Column(
            "paid_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_payments_invoice_id", "payments", ["invoice_id"])
    op.create_index("ix_payments_retailer_id", "payments", ["retailer_id"])
    op.create_index("ix_payments_customer_id", "payments", ["customer_id"])

    # 6. Sales Returns
    op.create_table(
        "sales_returns",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "sales_order_id",
            sa.String(length=36),
            sa.ForeignKey("sales_orders.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "retailer_id",
            sa.String(length=36),
            sa.ForeignKey("retailers.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="requested"),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "requested_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_sales_returns_sales_order_id", "sales_returns", ["sales_order_id"])
    op.create_index("ix_sales_returns_retailer_id", "sales_returns", ["retailer_id"])

    # 7. Sales Return Items
    op.create_table(
        "sales_return_items",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "return_id",
            sa.String(length=36),
            sa.ForeignKey("sales_returns.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            sa.String(length=36),
            sa.ForeignKey("products.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("qty", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column(
            "batch_id",
            sa.String(length=36),
            sa.ForeignKey("stock_batches.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("condition", sa.String(length=50), nullable=False, server_default="resellable"),
    )
    op.create_index("ix_sales_return_items_return_id", "sales_return_items", ["return_id"])
    op.create_index("ix_sales_return_items_product_id", "sales_return_items", ["product_id"])

    # 8. Purchase Returns
    op.create_table(
        "purchase_returns",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "purchase_order_id",
            sa.String(length=36),
            sa.ForeignKey("purchase_orders.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "supplier_id",
            sa.String(length=36),
            sa.ForeignKey("suppliers.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="requested"),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "requested_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_purchase_returns_purchase_order_id",
        "purchase_returns",
        ["purchase_order_id"],
    )
    op.create_index("ix_purchase_returns_supplier_id", "purchase_returns", ["supplier_id"])

    # 9. Purchase Return Items
    op.create_table(
        "purchase_return_items",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "return_id",
            sa.String(length=36),
            sa.ForeignKey("purchase_returns.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            sa.String(length=36),
            sa.ForeignKey("products.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("qty", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column(
            "batch_id",
            sa.String(length=36),
            sa.ForeignKey("stock_batches.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reason", sa.String(length=255), nullable=True),
    )
    op.create_index(
        "ix_purchase_return_items_return_id",
        "purchase_return_items",
        ["return_id"],
    )
    op.create_index(
        "ix_purchase_return_items_product_id",
        "purchase_return_items",
        ["product_id"],
    )

    # 10. Deliveries
    op.create_table(
        "deliveries",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "sales_order_id",
            sa.String(length=36),
            sa.ForeignKey("sales_orders.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("driver_name", sa.String(length=100), nullable=True),
        sa.Column("vehicle_no", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="assigned"),
        sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_deliveries_sales_order_id", "deliveries", ["sales_order_id"])

    # 11. Roles
    op.create_table(
        "roles",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=50), nullable=False, unique=True),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_roles_name", "roles", ["name"])

    # 12. Permissions
    op.create_table(
        "permissions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=100), nullable=False, unique=True),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_permissions_code", "permissions", ["code"])

    # 13. Role Permissions
    op.create_table(
        "role_permissions",
        sa.Column(
            "role_id",
            sa.String(length=36),
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "permission_id",
            sa.String(length=36),
            sa.ForeignKey("permissions.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    # 14. Stock Subscriptions
    op.create_table(
        "stock_subscriptions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "retailer_id",
            sa.String(length=36),
            sa.ForeignKey("retailers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            sa.String(length=36),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "channel_preference",
            sa.String(length=50),
            nullable=False,
            server_default="both",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("notified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.create_index(
        "ix_stock_subscriptions_retailer_id",
        "stock_subscriptions",
        ["retailer_id"],
    )
    op.create_index(
        "ix_stock_subscriptions_product_id",
        "stock_subscriptions",
        ["product_id"],
    )

    # 15. Supplier Access Tokens (Magic Links)
    op.create_table(
        "supplier_access_tokens",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "supplier_id",
            sa.String(length=36),
            sa.ForeignKey("suppliers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "purchase_order_id",
            sa.String(length=36),
            sa.ForeignKey("purchase_orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token", sa.String(length=100), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_supplier_access_tokens_token", "supplier_access_tokens", ["token"])
    op.create_index(
        "ix_supplier_access_tokens_supplier_id",
        "supplier_access_tokens",
        ["supplier_id"],
    )
    op.create_index(
        "ix_supplier_access_tokens_purchase_order_id",
        "supplier_access_tokens",
        ["purchase_order_id"],
    )

    # 16. Product Inquiries
    op.create_table(
        "product_inquiries",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "product_id",
            sa.String(length=36),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "retailer_id",
            sa.String(length=36),
            sa.ForeignKey("retailers.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "customer_id",
            sa.String(length=36),
            sa.ForeignKey("customers.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="open"),
        sa.Column("response", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_product_inquiries_product_id", "product_inquiries", ["product_id"])
    op.create_index("ix_product_inquiries_retailer_id", "product_inquiries", ["retailer_id"])
    op.create_index("ix_product_inquiries_customer_id", "product_inquiries", ["customer_id"])

    # 17. Batch Recalls
    op.create_table(
        "batch_recalls",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "batch_id",
            sa.String(length=36),
            sa.ForeignKey("stock_batches.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            sa.String(length=36),
            sa.ForeignKey("products.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=50), nullable=False, server_default="medium"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="initiated"),
        sa.Column(
            "initiated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_batch_recalls_batch_id", "batch_recalls", ["batch_id"])
    op.create_index("ix_batch_recalls_product_id", "batch_recalls", ["product_id"])

    # 18. Recall Affected Orders
    op.create_table(
        "recall_affected_orders",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "recall_id",
            sa.String(length=36),
            sa.ForeignKey("batch_recalls.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "sales_order_id",
            sa.String(length=36),
            sa.ForeignKey("sales_orders.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "retailer_id",
            sa.String(length=36),
            sa.ForeignKey("retailers.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "customer_id",
            sa.String(length=36),
            sa.ForeignKey("customers.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("notified_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_recall_affected_orders_recall_id", "recall_affected_orders", ["recall_id"])
    op.create_index(
        "ix_recall_affected_orders_sales_order_id",
        "recall_affected_orders",
        ["sales_order_id"],
    )
    op.create_index(
        "ix_recall_affected_orders_retailer_id",
        "recall_affected_orders",
        ["retailer_id"],
    )
    op.create_index(
        "ix_recall_affected_orders_customer_id",
        "recall_affected_orders",
        ["customer_id"],
    )

    # 19. Admin Audit Log
    op.create_table(
        "admin_audit_log",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("actor_id", sa.String(length=100), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.String(length=100), nullable=False),
        sa.Column("before_value", sa.JSON(), nullable=True),
        sa.Column("after_value", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_admin_audit_log_actor_id", "admin_audit_log", ["actor_id"])
    op.create_index("ix_admin_audit_log_entity_type", "admin_audit_log", ["entity_type"])
    op.create_index("ix_admin_audit_log_entity_id", "admin_audit_log", ["entity_id"])
    op.create_index("ix_admin_audit_log_created_at", "admin_audit_log", ["created_at"])

    # 20. Business Settings
    op.create_table(
        "business_settings",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("business_name", sa.String(length=255), nullable=False),
        sa.Column("gstin", sa.String(length=50), nullable=True),
        sa.Column("fssai_license_no", sa.String(length=50), nullable=True),
        sa.Column("fssai_expiry_date", sa.Date(), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("email", sa.String(length=100), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("business_settings")
    op.drop_table("admin_audit_log")
    op.drop_table("recall_affected_orders")
    op.drop_table("batch_recalls")
    op.drop_table("product_inquiries")
    op.drop_table("supplier_access_tokens")
    op.drop_table("stock_subscriptions")
    op.drop_table("role_permissions")
    op.drop_table("permissions")
    op.drop_table("roles")
    op.drop_table("deliveries")
    op.drop_table("purchase_return_items")
    op.drop_table("purchase_returns")
    op.drop_table("sales_return_items")
    op.drop_table("sales_returns")
    op.drop_table("payments")
    op.drop_table("invoice_items")
    op.drop_table("invoices")

    op.drop_index("ix_sales_orders_customer_id", "sales_orders")
    op.drop_index("ix_sales_orders_retailer_id", "sales_orders")
    op.alter_column("sales_orders", "retailer_id", nullable=False)
    op.drop_column("sales_orders", "customer_id")
    op.drop_column("sales_orders", "buyer_type")

    op.drop_table("customers")
