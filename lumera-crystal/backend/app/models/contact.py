from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class ContactMessage(TimestampMixin, Base):
    __tablename__ = "contact_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(220), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    auto_reply_status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending", index=True)
    auto_reply_subject: Mapped[str] = mapped_column(String(220), nullable=False, default="")
    auto_reply_body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    auto_replied_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
