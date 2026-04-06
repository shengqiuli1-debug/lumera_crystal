from sqlalchemy import Float, Index, Integer, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class MediaAsset(TimestampMixin, Base):
    __tablename__ = "media_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    biz_type: Mapped[str] = mapped_column(String(60), nullable=False, default="unbound", index=True)
    biz_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    original_file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    media_kind: Mapped[str] = mapped_column(String(20), nullable=False, default="image", index=True)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    storage_type: Mapped[str] = mapped_column(String(30), nullable=False, default="db", index=True)
    binary_data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    alt_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    used_as_cover_products = relationship("Product", back_populates="cover_media", foreign_keys="Product.cover_media_id")
    product_gallery_links = relationship("ProductImage", back_populates="media", cascade="all, delete-orphan")


Index("ix_media_assets_biz", MediaAsset.biz_type, MediaAsset.biz_id)
Index("ix_media_assets_sha256_size", MediaAsset.sha256, MediaAsset.file_size)
