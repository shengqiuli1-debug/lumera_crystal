from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Product, ProductImage


class ProductRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def _with_media(stmt):
        return stmt.options(
            selectinload(Product.cover_media),
            selectinload(Product.gallery_links).selectinload(ProductImage.media),
        )

    def list(
        self,
        page: int,
        page_size: int,
        *,
        category_slug: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        color: str | None = None,
        intention: str | None = None,
        search: str | None = None,
    ) -> tuple[list[Product], int]:
        filters = [Product.status == "active"]

        if category_slug:
            filters.append(Product.category.has(slug=category_slug))
        if min_price is not None:
            filters.append(Product.price >= min_price)
        if max_price is not None:
            filters.append(Product.price <= max_price)
        if color:
            filters.append(Product.color.ilike(f"%{color}%"))
        if intention:
            filters.append(Product.intention.ilike(f"%{intention}%"))
        if search:
            filters.append(
                Product.name.ilike(f"%{search}%")
                | Product.subtitle.ilike(f"%{search}%")
                | Product.short_description.ilike(f"%{search}%")
            )

        where_clause = and_(*filters)
        total_stmt = select(func.count()).select_from(Product).where(where_clause)
        total = self.db.scalar(total_stmt) or 0

        stmt = (
            self._with_media(select(Product))
            .where(where_clause)
            .order_by(Product.is_featured.desc(), Product.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list(self.db.scalars(stmt))
        return items, total

    def get_by_slug(self, slug: str) -> Product | None:
        stmt = self._with_media(select(Product).where(Product.slug == slug, Product.status == "active"))
        return self.db.scalar(stmt)
