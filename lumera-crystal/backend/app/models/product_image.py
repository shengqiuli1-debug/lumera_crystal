from sqlalchemy import ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class ProductImage(TimestampMixin, Base):
    __tablename__ = "product_images"
    __table_args__ = (UniqueConstraint("product_id", "media_id", name="uq_product_images_product_media"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    media_id: Mapped[int] = mapped_column(ForeignKey("media_assets.id", ondelete="RESTRICT"), nullable=False, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    product = relationship("Product", back_populates="gallery_links")
    media = relationship("MediaAsset", back_populates="product_gallery_links")


Index("ix_product_images_product_sort", ProductImage.product_id, ProductImage.sort_order)
