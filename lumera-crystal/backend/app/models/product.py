from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Product(TimestampMixin, Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    slug: Mapped[str] = mapped_column(String(160), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    subtitle: Mapped[str] = mapped_column(String(220), nullable=False, default="")
    short_description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    full_description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    cover_media_id: Mapped[int | None] = mapped_column(
        ForeignKey("media_assets.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # Deprecated URL fields kept for backward compatibility during migration to media_assets.
    cover_image: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    gallery_images: Mapped[list[str]] = mapped_column(ARRAY(String(255)), nullable=False, default=list)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, index=True)
    crystal_type: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    color: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    origin: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    size: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    material: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    chakra: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    intention: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    is_featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_new: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active", index=True)

    category = relationship("Category", back_populates="products")
    cover_media = relationship("MediaAsset", back_populates="used_as_cover_products", foreign_keys=[cover_media_id])
    gallery_links = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")


Index("ix_products_price", Product.price)
Index("ix_products_color", Product.color)
Index("ix_products_intention", Product.intention)
