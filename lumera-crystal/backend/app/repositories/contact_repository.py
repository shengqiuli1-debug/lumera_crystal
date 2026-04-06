from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import ContactMessage


class ContactRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, *, name: str, email: str, subject: str, message: str) -> ContactMessage:
        item = ContactMessage(name=name, email=email, subject=subject, message=message)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update_auto_reply(
        self,
        item: ContactMessage,
        *,
        status: str,
        subject: str,
        body: str,
    ) -> ContactMessage:
        item.auto_reply_status = status
        item.auto_reply_subject = subject
        item.auto_reply_body = body
        if status in {"sent", "replied"}:
            item.auto_replied_at = datetime.now(timezone.utc)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item
