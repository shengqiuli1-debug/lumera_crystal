from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Post(TimestampMixin, Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    slug: Mapped[str] = mapped_column(String(180), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    cover_image: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    author: Mapped[str] = mapped_column(String(120), nullable=False, default="LUMERA 编辑部")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String(80)), nullable=False, default=list)
    seo_title: Mapped[str] = mapped_column(String(220), nullable=False, default="")
    seo_description: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft", index=True)


Index("ix_posts_published_at", Post.published_at)
