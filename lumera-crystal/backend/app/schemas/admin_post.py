from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

PostStatus = Literal["draft", "published", "archived"]


class AdminPostBase(BaseModel):
    slug: str = Field(min_length=1, max_length=180)
    title: str = Field(min_length=1, max_length=220)
    excerpt: str = ""
    cover_image: str = ""
    content: str = ""
    author: str = "LUMERA 编辑部"
    published_at: datetime | None = None
    tags: list[str] = Field(default_factory=list)
    seo_title: str = ""
    seo_description: str = ""
    status: PostStatus = "draft"


class AdminPostCreate(AdminPostBase):
    pass


class AdminPostUpdate(BaseModel):
    slug: str | None = Field(default=None, min_length=1, max_length=180)
    title: str | None = Field(default=None, min_length=1, max_length=220)
    excerpt: str | None = None
    cover_image: str | None = None
    content: str | None = None
    author: str | None = None
    published_at: datetime | None = None
    tags: list[str] | None = None
    seo_title: str | None = None
    seo_description: str | None = None
    status: PostStatus | None = None


class AdminPostRead(AdminPostBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AdminPostListResponse(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[AdminPostRead]
