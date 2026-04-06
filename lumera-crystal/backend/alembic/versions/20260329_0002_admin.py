"""add admin user and message read state

Revision ID: 20260329_0002
Revises: 20260329_0001
Create Date: 2026-03-29 18:10:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260329_0002"
down_revision = "20260329_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "admin_users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=180), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_admin_users_email", "admin_users", ["email"])
    op.create_index("ix_admin_users_is_active", "admin_users", ["is_active"])

    op.add_column("contact_messages", sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.create_index("ix_contact_messages_is_read", "contact_messages", ["is_read"])


def downgrade() -> None:
    op.drop_index("ix_contact_messages_is_read", table_name="contact_messages")
    op.drop_column("contact_messages", "is_read")
    op.drop_index("ix_admin_users_is_active", table_name="admin_users")
    op.drop_index("ix_admin_users_email", table_name="admin_users")
    op.drop_table("admin_users")
