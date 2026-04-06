from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Category, ContactMessage, Post, Product


class AdminDashboardRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def counts(self) -> dict[str, int]:
        return {
            "products_total": self.db.scalar(select(func.count()).select_from(Product)) or 0,
            "products_active": self.db.scalar(select(func.count()).select_from(Product).where(Product.status == "active")) or 0,
            "products_draft": self.db.scalar(select(func.count()).select_from(Product).where(Product.status == "draft")) or 0,
            "categories_total": self.db.scalar(select(func.count()).select_from(Category)) or 0,
            "posts_published": self.db.scalar(select(func.count()).select_from(Post).where(Post.status == "published")) or 0,
        }

    def recent_products(self, limit: int = 5) -> list[Product]:
        stmt = select(Product).order_by(Product.updated_at.desc()).limit(limit)
        return list(self.db.scalars(stmt))

    def latest_messages(self, limit: int = 5) -> list[ContactMessage]:
        stmt = select(ContactMessage).order_by(ContactMessage.created_at.desc()).limit(limit)
        return list(self.db.scalars(stmt))
