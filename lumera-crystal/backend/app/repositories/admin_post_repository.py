from sqlalchemy import and_, asc, desc, func, select
from sqlalchemy.orm import Session

from app.models import Post


class AdminPostRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None,
        status: str | None,
        sort_order: str,
    ) -> tuple[list[Post], int]:
        filters = []
        if search:
            filters.append(Post.title.ilike(f"%{search}%") | Post.slug.ilike(f"%{search}%") | Post.excerpt.ilike(f"%{search}%"))
        if status:
            filters.append(Post.status == status)
        where_clause = and_(*filters) if filters else None

        total_stmt = select(func.count()).select_from(Post)
        if where_clause is not None:
            total_stmt = total_stmt.where(where_clause)
        total = self.db.scalar(total_stmt) or 0

        order_clause = asc(Post.updated_at) if sort_order == "asc" else desc(Post.updated_at)
        stmt = select(Post)
        if where_clause is not None:
            stmt = stmt.where(where_clause)
        stmt = stmt.order_by(order_clause, Post.id.desc()).offset((page - 1) * page_size).limit(page_size)
        return list(self.db.scalars(stmt)), total

    def get(self, post_id: int) -> Post | None:
        return self.db.get(Post, post_id)

    def get_by_slug(self, slug: str) -> Post | None:
        return self.db.scalar(select(Post).where(Post.slug == slug))

    def create(self, payload: dict) -> Post:
        item = Post(**payload)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update(self, item: Post, payload: dict) -> Post:
        for key, value in payload.items():
            setattr(item, key, value)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete(self, item: Post) -> None:
        self.db.delete(item)
        self.db.commit()
