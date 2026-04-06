from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models import AdminUser
from app.repositories.admin_category_repository import AdminCategoryRepository
from app.schemas.admin_category import AdminCategoryCreate, AdminCategoryRead, AdminCategoryUpdate
from app.services.admin_category_service import AdminCategoryService

router = APIRouter(prefix="/categories", tags=["admin-categories"])


@router.get("", response_model=list[AdminCategoryRead])
def list_categories(
    search: str | None = None,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> list[AdminCategoryRead]:
    service = AdminCategoryService(AdminCategoryRepository(db))
    return service.list_categories(search=search)


@router.get("/{category_id}", response_model=AdminCategoryRead)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> AdminCategoryRead:
    service = AdminCategoryService(AdminCategoryRepository(db))
    return service.get_or_404(category_id)


@router.post("", response_model=AdminCategoryRead)
def create_category(
    payload: AdminCategoryCreate,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> AdminCategoryRead:
    service = AdminCategoryService(AdminCategoryRepository(db))
    return service.create_category(payload.model_dump())


@router.patch("/{category_id}", response_model=AdminCategoryRead)
def update_category(
    category_id: int,
    payload: AdminCategoryUpdate,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> AdminCategoryRead:
    service = AdminCategoryService(AdminCategoryRepository(db))
    return service.update_category(category_id, payload.model_dump(exclude_unset=True))


@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> dict:
    service = AdminCategoryService(AdminCategoryRepository(db))
    service.delete_category(category_id)
    return {"success": True}
