from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.newsletter_repository import NewsletterRepository
from app.schemas.newsletter import NewsletterCreate, NewsletterRead
from app.services.newsletter_service import NewsletterService

router = APIRouter(prefix="/newsletter", tags=["newsletter"])


@router.post("", response_model=NewsletterRead, status_code=status.HTTP_201_CREATED)
def subscribe(payload: NewsletterCreate, db: Session = Depends(get_db)) -> NewsletterRead:
    service = NewsletterService(NewsletterRepository(db))
    subscriber, _ = service.subscribe(payload)
    return subscriber
