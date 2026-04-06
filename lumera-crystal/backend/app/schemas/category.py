from datetime import datetime

from pydantic import BaseModel


class CategoryBase(BaseModel):
    name: str
    slug: str
    description: str
    cover_image: str
    sort_order: int


class CategoryRead(CategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
