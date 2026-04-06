from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryRead
from app.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryRead])
def list_categories(db: Session = Depends(get_db)) -> list[CategoryRead]:
    service = CategoryService(CategoryRepository(db))
    return service.list_categories()


@router.get("/{slug}", response_model=CategoryRead)
def get_category(slug: str, db: Session = Depends(get_db)) -> CategoryRead:
    service = CategoryService(CategoryRepository(db))
    item = service.get_by_slug(slug)
    if not item:
        raise HTTPException(status_code=404, detail="Category not found")
    return item
