from sqlalchemy import asc, func, select
from sqlalchemy.orm import Session

from app.models import Category, Product


class AdminCategoryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self, *, search: str | None = None) -> list[Category]:
        stmt = select(Category)
        if search:
            stmt = stmt.where(Category.name.ilike(f"%{search}%") | Category.slug.ilike(f"%{search}%"))
        stmt = stmt.order_by(asc(Category.sort_order), Category.id.asc())
        return list(self.db.scalars(stmt))

    def get(self, category_id: int) -> Category | None:
        return self.db.get(Category, category_id)

    def get_by_slug(self, slug: str) -> Category | None:
        return self.db.scalar(select(Category).where(Category.slug == slug))

    def create(self, payload: dict) -> Category:
        item = Category(**payload)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update(self, item: Category, payload: dict) -> Category:
        for key, value in payload.items():
            setattr(item, key, value)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete(self, item: Category) -> None:
        self.db.delete(item)
        self.db.commit()

    def count_products(self, category_id: int) -> int:
        return self.db.scalar(select(func.count()).select_from(Product).where(Product.category_id == category_id)) or 0
