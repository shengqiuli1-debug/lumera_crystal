from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models import AdminUser
from app.repositories.admin_category_repository import AdminCategoryRepository
from app.repositories.admin_product_repository import AdminProductRepository
from app.repositories.media_repository import MediaRepository
from app.schemas.admin_product import (
    AdminBulkActionResponse,
    AdminProductBulkStatusRequest,
    AdminProductCreate,
    AdminProductListResponse,
    AdminProductRead,
    AdminProductUpdate,
    ProductSortBy,
    ProductStatus,
    SortOrder,
)
from app.services.admin_product_service import AdminProductService
from app.services.media_service import MediaService, to_media_read
from app.services.storage.db_storage import DatabaseStorageService

router = APIRouter(prefix="/products", tags=["admin-products"])


def _build_service(db: Session) -> AdminProductService:
    media_repo = MediaRepository(db)
    return AdminProductService(
        AdminProductRepository(db),
        AdminCategoryRepository(db),
        media_repo,
        MediaService(media_repo, DatabaseStorageService()),
    )


def _to_admin_product_read(item) -> AdminProductRead:
    cover = to_media_read(item.cover_media) if item.cover_media else None
    gallery_links = sorted(item.gallery_links, key=lambda link: link.sort_order)
    gallery_assets = [to_media_read(link.media) for link in gallery_links if link.media]
    base = AdminProductRead.model_validate(item, from_attributes=True)
    return base.model_copy(
        update={
            "cover_media_id": item.cover_media_id,
            "gallery_media_ids": [link.media_id for link in gallery_links],
            "cover_image_asset": cover,
            "gallery_image_assets": gallery_assets,
            "cover_image": cover.url if cover else "",
            "gallery_images": [asset.url for asset in gallery_assets],
        }
    )


@router.get("", response_model=AdminProductListResponse)
def list_products(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    status: ProductStatus | None = None,
    category_id: int | None = None,
    is_featured: bool | None = None,
    is_new: bool | None = None,
    sort_by: ProductSortBy = "updated_at",
    sort_order: SortOrder = "desc",
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> AdminProductListResponse:
    service = _build_service(db)
    items, total = service.list_products(
        page=page,
        page_size=page_size,
        search=search,
        status=status,
        category_id=category_id,
        is_featured=is_featured,
        is_new=is_new,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return AdminProductListResponse(
        page=page,
        page_size=page_size,
        total=total,
        items=[_to_admin_product_read(item) for item in items],
    )


@router.post("/bulk-status", response_model=AdminBulkActionResponse)
def bulk_status(
    payload: AdminProductBulkStatusRequest,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> AdminBulkActionResponse:
    service = _build_service(db)
    updated = service.bulk_update_status(payload.ids, payload.status)
    return AdminBulkActionResponse(updated_count=updated)


@router.get("/{product_id}", response_model=AdminProductRead)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> AdminProductRead:
    service = _build_service(db)
    return _to_admin_product_read(service.get_or_404(product_id))


@router.post("", response_model=AdminProductRead)
def create_product(
    payload: AdminProductCreate,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> AdminProductRead:
    service = _build_service(db)
    created = service.create_product(payload.model_dump())
    return _to_admin_product_read(created)


@router.patch("/{product_id}", response_model=AdminProductRead)
def update_product(
    product_id: int,
    payload: AdminProductUpdate,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> AdminProductRead:
    service = _build_service(db)
    updates = payload.model_dump(exclude_unset=True)
    updated = service.update_product(product_id, updates)
    return _to_admin_product_read(updated)


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> dict:
    service = _build_service(db)
    service.delete_product(product_id)
    return {"success": True}
