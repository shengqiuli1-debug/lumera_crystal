from sqlalchemy import and_, desc, func, select
from sqlalchemy.orm import Session

from app.models import ContactMessage
from app.repositories.contact_repository import ContactRepository


class AdminMessageRepository:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.contact_repo = ContactRepository(db)

    def list(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        is_read: bool | None = None,
    ) -> tuple[list[ContactMessage], int]:
        filters = []
        if search:
            filters.append(
                ContactMessage.name.ilike(f"%{search}%")
                | ContactMessage.email.ilike(f"%{search}%")
                | ContactMessage.subject.ilike(f"%{search}%")
            )
        if is_read is not None:
            filters.append(ContactMessage.is_read == is_read)
        where_clause = and_(*filters) if filters else None

        total_stmt = select(func.count()).select_from(ContactMessage)
        if where_clause is not None:
            total_stmt = total_stmt.where(where_clause)
        total = self.db.scalar(total_stmt) or 0

        stmt = select(ContactMessage)
        if where_clause is not None:
            stmt = stmt.where(where_clause)
        stmt = stmt.order_by(desc(ContactMessage.created_at)).offset((page - 1) * page_size).limit(page_size)
        return list(self.db.scalars(stmt)), total

    def get(self, message_id: int) -> ContactMessage | None:
        return self.db.get(ContactMessage, message_id)

    def mark_read(self, item: ContactMessage, *, is_read: bool = True) -> ContactMessage:
        item.is_read = is_read
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def mark_replied(self, item: ContactMessage, *, subject: str, body: str) -> ContactMessage:
        item.is_read = True
        return self.contact_repo.update_auto_reply(item, status="replied", subject=subject, body=body)
