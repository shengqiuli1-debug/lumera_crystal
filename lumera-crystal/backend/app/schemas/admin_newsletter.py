from datetime import datetime

from pydantic import BaseModel


class AdminNewsletterRead(BaseModel):
    id: int
    email: str
    source: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AdminNewsletterListResponse(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[AdminNewsletterRead]
