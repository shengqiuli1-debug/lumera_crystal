from datetime import datetime

from pydantic import BaseModel


class PostRead(BaseModel):
    id: int
    slug: str
    title: str
    excerpt: str
    cover_image: str
    content: str
    author: str
    published_at: datetime | None
    tags: list[str]
    seo_title: str
    seo_description: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PostListResponse(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[PostRead]
