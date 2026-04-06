from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models import AdminUser
from app.repositories.admin_message_repository import AdminMessageRepository
from app.schemas.admin_message import (
    AdminMessageListResponse,
    AdminMessageRead,
    AdminMessageReplyRequest,
    MarkMessageReadRequest,
)
from app.services.admin_message_service import AdminMessageService

router = APIRouter(prefix="/messages", tags=["admin-messages"])


@router.get("", response_model=AdminMessageListResponse)
def list_messages(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    is_read: bool | None = None,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> AdminMessageListResponse:
    service = AdminMessageService(AdminMessageRepository(db))
    items, total = service.list_messages(page=page, page_size=page_size, search=search, is_read=is_read)
    return AdminMessageListResponse(page=page, page_size=page_size, total=total, items=items)


@router.get("/{message_id}", response_model=AdminMessageRead)
def get_message(
    message_id: int,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> AdminMessageRead:
    service = AdminMessageService(AdminMessageRepository(db))
    return service.get_or_404(message_id)


@router.patch("/{message_id}/read", response_model=AdminMessageRead)
def mark_message_read(
    message_id: int,
    payload: MarkMessageReadRequest,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> AdminMessageRead:
    service = AdminMessageService(AdminMessageRepository(db))
    return service.mark_read(message_id, is_read=payload.is_read)


@router.post("/{message_id}/reply", response_model=AdminMessageRead)
def reply_message(
    message_id: int,
    payload: AdminMessageReplyRequest,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> AdminMessageRead:
    service = AdminMessageService(AdminMessageRepository(db))
    return service.reply_to_message(message_id, reply_content=payload.reply_content)
