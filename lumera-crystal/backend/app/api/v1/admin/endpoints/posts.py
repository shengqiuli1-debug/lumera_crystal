from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models import AdminUser
from app.repositories.admin_post_repository import AdminPostRepository
from app.schemas.admin_post import AdminPostCreate, AdminPostListResponse, AdminPostRead, AdminPostUpdate, PostStatus
from app.services.admin_post_service import AdminPostService

router = APIRouter(prefix="/posts", tags=["admin-posts"])


@router.get("", response_model=AdminPostListResponse)
def list_posts(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    status: PostStatus | None = None,
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> AdminPostListResponse:
    service = AdminPostService(AdminPostRepository(db))
    items, total = service.list_posts(
        page=page,
        page_size=page_size,
        search=search,
        status=status,
        sort_order=sort_order,
    )
    return AdminPostListResponse(page=page, page_size=page_size, total=total, items=items)


@router.get("/{post_id}", response_model=AdminPostRead)
def get_post(post_id: int, db: Session = Depends(get_db), _: AdminUser = Depends(get_current_admin)) -> AdminPostRead:
    service = AdminPostService(AdminPostRepository(db))
    return service.get_or_404(post_id)


@router.post("", response_model=AdminPostRead)
def create_post(
    payload: AdminPostCreate,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> AdminPostRead:
    service = AdminPostService(AdminPostRepository(db))
    return service.create_post(payload.model_dump())


@router.patch("/{post_id}", response_model=AdminPostRead)
def update_post(
    post_id: int,
    payload: AdminPostUpdate,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> AdminPostRead:
    service = AdminPostService(AdminPostRepository(db))
    return service.update_post(post_id, payload.model_dump(exclude_unset=True))


@router.delete("/{post_id}")
def delete_post(post_id: int, db: Session = Depends(get_db), _: AdminUser = Depends(get_current_admin)) -> dict:
    service = AdminPostService(AdminPostRepository(db))
    service.delete_post(post_id)
    return {"success": True}
