"""add shop payment attempts table

Revision ID: 20260416_0006
Revises: 20260403_0005
Create Date: 2026-04-16 21:30:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260416_0006"
down_revision = "20260403_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "shop_payments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("payment_no", sa.String(length=50), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("method", sa.String(length=30), nullable=False, server_default="mock"),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="initiated"),
        sa.Column("payment_reference", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("failure_reason", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("raw_payload", sa.Text(), nullable=False, server_default=""),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["shop_orders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("payment_no", name="uq_shop_payments_payment_no"),
    )
    op.create_index("ix_shop_payments_id", "shop_payments", ["id"])
    op.create_index("ix_shop_payments_payment_no", "shop_payments", ["payment_no"])
    op.create_index("ix_shop_payments_order_id", "shop_payments", ["order_id"])
    op.create_index("ix_shop_payments_status", "shop_payments", ["status"])
    op.create_index("ix_shop_payments_order_created_at", "shop_payments", ["order_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_shop_payments_order_created_at", table_name="shop_payments")
    op.drop_index("ix_shop_payments_status", table_name="shop_payments")
    op.drop_index("ix_shop_payments_order_id", table_name="shop_payments")
    op.drop_index("ix_shop_payments_payment_no", table_name="shop_payments")
    op.drop_index("ix_shop_payments_id", table_name="shop_payments")
    op.drop_table("shop_payments")
