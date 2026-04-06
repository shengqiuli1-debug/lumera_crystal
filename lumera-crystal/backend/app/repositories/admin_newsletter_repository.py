from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models import NewsletterSubscriber


class AdminNewsletterRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self, *, page: int, page_size: int, search: str | None = None) -> tuple[list[NewsletterSubscriber], int]:
        stmt = select(NewsletterSubscriber)
        count_stmt = select(func.count()).select_from(NewsletterSubscriber)
        if search:
            filter_expr = NewsletterSubscriber.email.ilike(f"%{search}%")
            stmt = stmt.where(filter_expr)
            count_stmt = count_stmt.where(filter_expr)

        total = self.db.scalar(count_stmt) or 0
        stmt = stmt.order_by(desc(NewsletterSubscriber.created_at)).offset((page - 1) * page_size).limit(page_size)
        return list(self.db.scalars(stmt)), total
