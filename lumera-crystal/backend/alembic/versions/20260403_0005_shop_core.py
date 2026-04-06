"""add lightweight shop core tables

Revision ID: 20260403_0005
Revises: 20260329_0004
Create Date: 2026-04-03 10:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260403_0005"
down_revision = "20260329_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "shop_users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=180), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("points_balance", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_shop_users_email"),
    )
    op.create_index("ix_shop_users_id", "shop_users", ["id"])
    op.create_index("ix_shop_users_email", "shop_users", ["email"])
    op.create_index("ix_shop_users_is_active", "shop_users", ["is_active"])

    op.create_table(
        "coupons",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=60), nullable=False),
        sa.Column("discount_type", sa.String(length=20), nullable=False, server_default="percent"),
        sa.Column("discount_value", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("min_order_amount", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("usage_limit", sa.Integer(), nullable=True),
        sa.Column("used_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_coupons_code"),
    )
    op.create_index("ix_coupons_id", "coupons", ["id"])
    op.create_index("ix_coupons_code", "coupons", ["code"])
    op.create_index("ix_coupons_is_active", "coupons", ["is_active"])

    op.create_table(
        "shop_orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_no", sa.String(length=40), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="created"),
        sa.Column("payment_status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("shipping_status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("coupon_code", sa.String(length=60), nullable=True),
        sa.Column("points_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("subtotal_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("discount_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("shipping_address", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["shop_users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_no", name="uq_shop_orders_order_no"),
    )
    op.create_index("ix_shop_orders_id", "shop_orders", ["id"])
    op.create_index("ix_shop_orders_order_no", "shop_orders", ["order_no"])
    op.create_index("ix_shop_orders_user_id", "shop_orders", ["user_id"])
    op.create_index("ix_shop_orders_status", "shop_orders", ["status"])
    op.create_index("ix_shop_orders_payment_status", "shop_orders", ["payment_status"])
    op.create_index("ix_shop_orders_shipping_status", "shop_orders", ["shipping_status"])
    op.create_index("ix_shop_orders_user_paid_at", "shop_orders", ["user_id", "paid_at"])

    op.create_table(
        "shop_order_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("line_total", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["order_id"], ["shop_orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_id", "product_id", name="uq_shop_order_items_order_product"),
    )
    op.create_index("ix_shop_order_items_order_id", "shop_order_items", ["order_id"])
    op.create_index("ix_shop_order_items_product_id", "shop_order_items", ["product_id"])

    op.create_table(
        "inventory_alerts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("threshold", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("stock_snapshot", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="open"),
        sa.Column("message", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_inventory_alerts_id", "inventory_alerts", ["id"])
    op.create_index("ix_inventory_alerts_product_id", "inventory_alerts", ["product_id"])
    op.create_index("ix_inventory_alerts_status", "inventory_alerts", ["status"])

    op.create_table(
        "restock_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("requested_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("external_ref", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("provider_response", sa.Text(), nullable=False, server_default=""),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_restock_requests_id", "restock_requests", ["id"])
    op.create_index("ix_restock_requests_product_id", "restock_requests", ["product_id"])
    op.create_index("ix_restock_requests_status", "restock_requests", ["status"])
    op.create_index("ix_restock_requests_product_status", "restock_requests", ["product_id", "status"])

    op.create_table(
        "shipment_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("carrier", sa.String(length=80), nullable=False, server_default="mock-express"),
        sa.Column("tracking_no", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("payload", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["shop_orders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_shipment_requests_id", "shipment_requests", ["id"])
    op.create_index("ix_shipment_requests_order_id", "shipment_requests", ["order_id"])
    op.create_index("ix_shipment_requests_status", "shipment_requests", ["status"])

    op.create_table(
        "user_behavior_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=30), nullable=False),
        sa.Column("weight", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["shop_users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_behavior_events_id", "user_behavior_events", ["id"])
    op.create_index("ix_user_behavior_events_user_id", "user_behavior_events", ["user_id"])
    op.create_index("ix_user_behavior_events_product_id", "user_behavior_events", ["product_id"])
    op.create_index("ix_user_behavior_events_event_type", "user_behavior_events", ["event_type"])


def downgrade() -> None:
    op.drop_index("ix_user_behavior_events_event_type", table_name="user_behavior_events")
    op.drop_index("ix_user_behavior_events_product_id", table_name="user_behavior_events")
    op.drop_index("ix_user_behavior_events_user_id", table_name="user_behavior_events")
    op.drop_index("ix_user_behavior_events_id", table_name="user_behavior_events")
    op.drop_table("user_behavior_events")

    op.drop_index("ix_shipment_requests_status", table_name="shipment_requests")
    op.drop_index("ix_shipment_requests_order_id", table_name="shipment_requests")
    op.drop_index("ix_shipment_requests_id", table_name="shipment_requests")
    op.drop_table("shipment_requests")

    op.drop_index("ix_restock_requests_product_status", table_name="restock_requests")
    op.drop_index("ix_restock_requests_status", table_name="restock_requests")
    op.drop_index("ix_restock_requests_product_id", table_name="restock_requests")
    op.drop_index("ix_restock_requests_id", table_name="restock_requests")
    op.drop_table("restock_requests")

    op.drop_index("ix_inventory_alerts_status", table_name="inventory_alerts")
    op.drop_index("ix_inventory_alerts_product_id", table_name="inventory_alerts")
    op.drop_index("ix_inventory_alerts_id", table_name="inventory_alerts")
    op.drop_table("inventory_alerts")

    op.drop_index("ix_shop_order_items_product_id", table_name="shop_order_items")
    op.drop_index("ix_shop_order_items_order_id", table_name="shop_order_items")
    op.drop_table("shop_order_items")

    op.drop_index("ix_shop_orders_user_paid_at", table_name="shop_orders")
    op.drop_index("ix_shop_orders_shipping_status", table_name="shop_orders")
    op.drop_index("ix_shop_orders_payment_status", table_name="shop_orders")
    op.drop_index("ix_shop_orders_status", table_name="shop_orders")
    op.drop_index("ix_shop_orders_user_id", table_name="shop_orders")
    op.drop_index("ix_shop_orders_order_no", table_name="shop_orders")
    op.drop_index("ix_shop_orders_id", table_name="shop_orders")
    op.drop_table("shop_orders")

    op.drop_index("ix_coupons_is_active", table_name="coupons")
    op.drop_index("ix_coupons_code", table_name="coupons")
    op.drop_index("ix_coupons_id", table_name="coupons")
    op.drop_table("coupons")

    op.drop_index("ix_shop_users_is_active", table_name="shop_users")
    op.drop_index("ix_shop_users_email", table_name="shop_users")
    op.drop_index("ix_shop_users_id", table_name="shop_users")
    op.drop_table("shop_users")
