from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.contact_repository import ContactRepository
from app.schemas.contact import ContactCreate, ContactRead
from app.services.contact_service import ContactService

router = APIRouter(prefix="/contact", tags=["contact"])


@router.post("", response_model=ContactRead, status_code=status.HTTP_201_CREATED)
def create_contact(payload: ContactCreate, db: Session = Depends(get_db)) -> ContactRead:
    service = ContactService(ContactRepository(db))
    return service.create_message(payload)
