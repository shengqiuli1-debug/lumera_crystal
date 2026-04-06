from datetime import datetime

from pydantic import BaseModel, Field


class AdminCategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    slug: str = Field(min_length=1, max_length=120)
    description: str = ""
    cover_image: str = ""
    sort_order: int = 0


class AdminCategoryCreate(AdminCategoryBase):
    pass


class AdminCategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    slug: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    cover_image: str | None = None
    sort_order: int | None = None


class AdminCategoryRead(AdminCategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
