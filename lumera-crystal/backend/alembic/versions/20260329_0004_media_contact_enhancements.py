"""add media duration/kind and contact auto reply fields

Revision ID: 20260329_0004
Revises: 20260329_0003
Create Date: 2026-03-29 22:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260329_0004"
down_revision = "20260329_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("media_assets", sa.Column("media_kind", sa.String(length=20), nullable=False, server_default="image"))
    op.add_column("media_assets", sa.Column("duration_seconds", sa.Float(), nullable=True))
    op.create_index("ix_media_assets_media_kind", "media_assets", ["media_kind"])

    op.add_column(
        "contact_messages",
        sa.Column("auto_reply_status", sa.String(length=30), nullable=False, server_default="pending"),
    )
    op.add_column("contact_messages", sa.Column("auto_reply_subject", sa.String(length=220), nullable=False, server_default=""))
    op.add_column("contact_messages", sa.Column("auto_reply_body", sa.Text(), nullable=False, server_default=""))
    op.add_column("contact_messages", sa.Column("auto_replied_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_contact_messages_auto_reply_status", "contact_messages", ["auto_reply_status"])


def downgrade() -> None:
    op.drop_index("ix_contact_messages_auto_reply_status", table_name="contact_messages")
    op.drop_column("contact_messages", "auto_replied_at")
    op.drop_column("contact_messages", "auto_reply_body")
    op.drop_column("contact_messages", "auto_reply_subject")
    op.drop_column("contact_messages", "auto_reply_status")

    op.drop_index("ix_media_assets_media_kind", table_name="media_assets")
    op.drop_column("media_assets", "duration_seconds")
    op.drop_column("media_assets", "media_kind")
