from __future__ import annotations

from sqlalchemy import and_, asc, desc, func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Product, ProductImage
from app.services.media_service import build_media_url


class AdminProductRepository:
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
        *,
        page: int,
        page_size: int,
        search: str | None,
        status: str | None,
        category_id: int | None,
        is_featured: bool | None,
        is_new: bool | None,
        sort_by: str,
        sort_order: str,
    ) -> tuple[list[Product], int]:
        filters = []
        if search:
            filters.append(
                Product.name.ilike(f"%{search}%")
                | Product.slug.ilike(f"%{search}%")
                | Product.subtitle.ilike(f"%{search}%")
            )
        if status:
            filters.append(Product.status == status)
        if category_id is not None:
            filters.append(Product.category_id == category_id)
        if is_featured is not None:
            filters.append(Product.is_featured == is_featured)
        if is_new is not None:
            filters.append(Product.is_new == is_new)

        where_clause = and_(*filters) if filters else None
        total_stmt = select(func.count()).select_from(Product)
        if where_clause is not None:
            total_stmt = total_stmt.where(where_clause)
        total = self.db.scalar(total_stmt) or 0

        sort_field = getattr(Product, sort_by, Product.updated_at)
        sort_clause = asc(sort_field) if sort_order == "asc" else desc(sort_field)
        stmt = self._with_media(select(Product))
        if where_clause is not None:
            stmt = stmt.where(where_clause)
        stmt = stmt.order_by(sort_clause, Product.id.desc()).offset((page - 1) * page_size).limit(page_size)
        return list(self.db.scalars(stmt)), total

    def get(self, product_id: int) -> Product | None:
        stmt = self._with_media(select(Product).where(Product.id == product_id))
        return self.db.scalar(stmt)

    def get_by_slug(self, slug: str) -> Product | None:
        return self.db.scalar(select(Product).where(Product.slug == slug))

    def create(self, payload: dict, *, gallery_media_ids: list[int] | None = None) -> Product:
        cover_media_id = payload.get("cover_media_id")
        payload["cover_image"] = build_media_url(cover_media_id) if cover_media_id else payload.get("cover_image", "")
        payload["gallery_images"] = [build_media_url(media_id) for media_id in (gallery_media_ids or [])]
        item = Product(**payload)
        self.db.add(item)
        self.db.flush()

        if gallery_media_ids:
            self.db.add_all(
                [
                    ProductImage(product_id=item.id, media_id=media_id, sort_order=index)
                    for index, media_id in enumerate(gallery_media_ids)
                ]
            )
        self.db.commit()
        return self.get(item.id) or item

    def update(self, item: Product, payload: dict, *, gallery_media_ids: list[int] | None = None) -> Product:
        cover_media_id = payload.get("cover_media_id", item.cover_media_id)
        payload["cover_image"] = build_media_url(cover_media_id) if cover_media_id else payload.get("cover_image", "")
        if gallery_media_ids is not None:
            payload["gallery_images"] = [build_media_url(media_id) for media_id in gallery_media_ids]

        for key, value in payload.items():
            setattr(item, key, value)

        if gallery_media_ids is not None:
            item.gallery_links.clear()
            self.db.flush()
            if gallery_media_ids:
                item.gallery_links.extend(
                    [
                        ProductImage(product_id=item.id, media_id=media_id, sort_order=index)
                        for index, media_id in enumerate(gallery_media_ids)
                    ]
                )
        self.db.commit()
        return self.get(item.id) or item

    def delete(self, item: Product) -> None:
        self.db.delete(item)
        self.db.commit()

    def bulk_update_status(self, ids: list[int], status: str) -> int:
        stmt = select(Product).where(Product.id.in_(ids))
        items = list(self.db.scalars(stmt))
        for item in items:
            item.status = status
            self.db.add(item)
        self.db.commit()
        return len(items)
