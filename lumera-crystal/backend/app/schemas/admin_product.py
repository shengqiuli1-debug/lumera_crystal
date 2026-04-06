from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.media import MediaAssetRead


ProductStatus = Literal["draft", "active", "archived"]
ProductSortBy = Literal["updated_at", "created_at", "name", "price", "stock"]
SortOrder = Literal["asc", "desc"]


class AdminProductBase(BaseModel):
    slug: str = Field(min_length=1, max_length=160)
    name: str = Field(min_length=1, max_length=180)
    subtitle: str = ""
    short_description: str = ""
    full_description: str = ""
    price: Decimal = Field(default=Decimal("0"))
    cover_media_id: int | None = None
    gallery_media_ids: list[int] = Field(default_factory=list)
    cover_image: str = ""
    gallery_images: list[str] = Field(default_factory=list)
    stock: int = 0
    category_id: int
    crystal_type: str = ""
    color: str = ""
    origin: str = ""
    size: str = ""
    material: str = ""
    chakra: str = ""
    intention: str = ""
    is_featured: bool = False
    is_new: bool = False
    status: ProductStatus = "draft"


class AdminProductCreate(AdminProductBase):
    pass


class AdminProductUpdate(BaseModel):
    slug: str | None = Field(default=None, min_length=1, max_length=160)
    name: str | None = Field(default=None, min_length=1, max_length=180)
    subtitle: str | None = None
    short_description: str | None = None
    full_description: str | None = None
    price: Decimal | None = None
    cover_media_id: int | None = None
    gallery_media_ids: list[int] | None = None
    cover_image: str | None = None
    gallery_images: list[str] | None = None
    stock: int | None = None
    category_id: int | None = None
    crystal_type: str | None = None
    color: str | None = None
    origin: str | None = None
    size: str | None = None
    material: str | None = None
    chakra: str | None = None
    intention: str | None = None
    is_featured: bool | None = None
    is_new: bool | None = None
    status: ProductStatus | None = None


class AdminProductRead(AdminProductBase):
    id: int
    cover_image_asset: MediaAssetRead | None = None
    gallery_image_assets: list[MediaAssetRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AdminProductListResponse(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[AdminProductRead]


class AdminProductBulkStatusRequest(BaseModel):
    ids: list[int] = Field(min_length=1)
    status: ProductStatus


class AdminBulkActionResponse(BaseModel):
    updated_count: int
