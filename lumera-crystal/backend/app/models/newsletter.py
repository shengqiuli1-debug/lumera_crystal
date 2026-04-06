from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class NewsletterSubscriber(TimestampMixin, Base):
    __tablename__ = "newsletter_subscribers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(180), nullable=False, unique=True, index=True)
    source: Mapped[str] = mapped_column(String(80), nullable=False, default="website")
