from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models import Post


class PostRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self, page: int, page_size: int, search: str | None = None) -> tuple[list[Post], int]:
        filters = [Post.status == "published"]
        if search:
            filters.append(Post.title.ilike(f"%{search}%") | Post.excerpt.ilike(f"%{search}%"))

        where_clause = and_(*filters)
        total = self.db.scalar(select(func.count()).select_from(Post).where(where_clause)) or 0
        stmt = (
            select(Post)
            .where(where_clause)
            .order_by(Post.published_at.desc().nullslast(), Post.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.db.scalars(stmt)), total

    def get_by_slug(self, slug: str) -> Post | None:
        return self.db.scalar(select(Post).where(Post.slug == slug, Post.status == "published"))
