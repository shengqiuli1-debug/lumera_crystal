from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Category


class CategoryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self) -> list[Category]:
        stmt = select(Category).order_by(Category.sort_order.asc(), Category.id.asc())
        return list(self.db.scalars(stmt))

    def get_by_slug(self, slug: str) -> Category | None:
        return self.db.scalar(select(Category).where(Category.slug == slug))

    def get_by_id(self, category_id: int) -> Category | None:
        return self.db.scalar(select(Category).where(Category.id == category_id))

    def count(self) -> int:
        return self.db.scalar(select(func.count()).select_from(Category)) or 0
