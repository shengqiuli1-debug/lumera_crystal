"""add media assets and product image relations

Revision ID: 20260329_0003
Revises: 20260329_0002
Create Date: 2026-03-29 19:20:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260329_0003"
down_revision = "20260329_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "media_assets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("biz_type", sa.String(length=60), nullable=False, server_default="unbound"),
        sa.Column("biz_id", sa.Integer(), nullable=True),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("original_file_name", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=80), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("storage_type", sa.String(length=30), nullable=False, server_default="db"),
        sa.Column("binary_data", sa.LargeBinary(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("alt_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_media_assets_id", "media_assets", ["id"])
    op.create_index("ix_media_assets_biz_id", "media_assets", ["biz_id"])
    op.create_index("ix_media_assets_biz_type", "media_assets", ["biz_type"])
    op.create_index("ix_media_assets_mime_type", "media_assets", ["mime_type"])
    op.create_index("ix_media_assets_sha256", "media_assets", ["sha256"])
    op.create_index("ix_media_assets_storage_type", "media_assets", ["storage_type"])
    op.create_index("ix_media_assets_biz", "media_assets", ["biz_type", "biz_id"])
    op.create_index("ix_media_assets_sha256_size", "media_assets", ["sha256", "file_size"])

    op.add_column("products", sa.Column("cover_media_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_products_cover_media_id", "products", "media_assets", ["cover_media_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_products_cover_media_id", "products", ["cover_media_id"])

    op.create_table(
        "product_images",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("media_id", sa.Integer(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["media_id"], ["media_assets.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id", "media_id", name="uq_product_images_product_media"),
    )
    op.create_index("ix_product_images_id", "product_images", ["id"])
    op.create_index("ix_product_images_product_id", "product_images", ["product_id"])
    op.create_index("ix_product_images_media_id", "product_images", ["media_id"])
    op.create_index("ix_product_images_product_sort", "product_images", ["product_id", "sort_order"])


def downgrade() -> None:
    op.drop_index("ix_product_images_product_sort", table_name="product_images")
    op.drop_index("ix_product_images_media_id", table_name="product_images")
    op.drop_index("ix_product_images_product_id", table_name="product_images")
    op.drop_index("ix_product_images_id", table_name="product_images")
    op.drop_table("product_images")

    op.drop_index("ix_products_cover_media_id", table_name="products")
    op.drop_constraint("fk_products_cover_media_id", "products", type_="foreignkey")
    op.drop_column("products", "cover_media_id")

    op.drop_index("ix_media_assets_sha256_size", table_name="media_assets")
    op.drop_index("ix_media_assets_biz", table_name="media_assets")
    op.drop_index("ix_media_assets_storage_type", table_name="media_assets")
    op.drop_index("ix_media_assets_sha256", table_name="media_assets")
    op.drop_index("ix_media_assets_mime_type", table_name="media_assets")
    op.drop_index("ix_media_assets_biz_type", table_name="media_assets")
    op.drop_index("ix_media_assets_biz_id", table_name="media_assets")
    op.drop_index("ix_media_assets_id", table_name="media_assets")
    op.drop_table("media_assets")
