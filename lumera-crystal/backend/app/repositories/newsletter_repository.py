from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import NewsletterSubscriber


class NewsletterRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_email(self, email: str) -> NewsletterSubscriber | None:
        return self.db.scalar(select(NewsletterSubscriber).where(NewsletterSubscriber.email == email))

    def create(self, *, email: str, source: str) -> NewsletterSubscriber:
        item = NewsletterSubscriber(email=email, source=source)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item
