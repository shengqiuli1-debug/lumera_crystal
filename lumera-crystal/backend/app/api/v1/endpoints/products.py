from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductListResponse, ProductRead
from app.services.media_service import to_media_read
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["products"])


def _to_product_read(item) -> ProductRead:
    cover = to_media_read(item.cover_media) if item.cover_media else None
    gallery_links = sorted(item.gallery_links, key=lambda link: link.sort_order)
    gallery_assets = [to_media_read(link.media) for link in gallery_links if link.media]
    base = ProductRead.model_validate(item, from_attributes=True)
    return base.model_copy(
        update={
            "cover_image": cover.url if cover else "",
            "gallery_images": [asset.url for asset in gallery_assets],
            "cover_image_asset": cover,
            "gallery_image_assets": gallery_assets,
        }
    )


@router.get("", response_model=ProductListResponse)
def list_products(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=100),
    category: str | None = None,
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    color: str | None = None,
    intention: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
) -> ProductListResponse:
    service = ProductService(ProductRepository(db))
    items, total = service.list_products(
        page,
        page_size,
        category=category,
        min_price=min_price,
        max_price=max_price,
        color=color,
        intention=intention,
        search=search,
    )
    return ProductListResponse(page=page, page_size=page_size, total=total, items=[_to_product_read(item) for item in items])


@router.get("/{slug}", response_model=ProductRead)
def get_product(slug: str, db: Session = Depends(get_db)) -> ProductRead:
    service = ProductService(ProductRepository(db))
    item = service.get_product_by_slug(slug)
    if not item:
        raise HTTPException(status_code=404, detail="Product not found")
    return _to_product_read(item)
