from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.media import MediaAssetRead


class ProductRead(BaseModel):
    id: int
    slug: str
    name: str
    subtitle: str
    short_description: str
    full_description: str
    price: Decimal
    cover_image: str
    gallery_images: list[str]
    cover_image_asset: MediaAssetRead | None = None
    gallery_image_assets: list[MediaAssetRead] = Field(default_factory=list)
    stock: int
    category_id: int
    crystal_type: str
    color: str
    origin: str
    size: str
    material: str
    chakra: str
    intention: str
    is_featured: bool
    is_new: bool
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[ProductRead]
