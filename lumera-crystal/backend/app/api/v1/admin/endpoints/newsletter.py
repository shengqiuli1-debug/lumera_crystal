from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models import AdminUser
from app.repositories.admin_newsletter_repository import AdminNewsletterRepository
from app.schemas.admin_newsletter import AdminNewsletterListResponse
from app.services.admin_newsletter_service import AdminNewsletterService

router = APIRouter(prefix="/newsletter", tags=["admin-newsletter"])


@router.get("", response_model=AdminNewsletterListResponse)
def list_newsletter(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> AdminNewsletterListResponse:
    service = AdminNewsletterService(AdminNewsletterRepository(db))
    items, total = service.list_newsletter(page=page, page_size=page_size, search=search)
    return AdminNewsletterListResponse(page=page, page_size=page_size, total=total, items=items)
