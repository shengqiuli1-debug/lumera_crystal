from datetime import datetime

from pydantic import BaseModel, Field


class AdminMessageRead(BaseModel):
    id: int
    name: str
    email: str
    subject: str
    message: str
    is_read: bool
    auto_reply_status: str
    auto_reply_subject: str
    auto_reply_body: str
    auto_replied_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AdminMessageListResponse(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[AdminMessageRead]


class MarkMessageReadRequest(BaseModel):
    is_read: bool = True


class AdminMessageReplyRequest(BaseModel):
    reply_content: str = Field(min_length=2, max_length=5000)
