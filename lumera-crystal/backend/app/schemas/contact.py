from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class ContactCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    subject: str = Field(default="网站咨询", min_length=2, max_length=220)
    message: str = Field(min_length=1, max_length=5000)


class ContactRead(BaseModel):
    id: int
    name: str
    email: EmailStr
    subject: str
    message: str
    auto_reply_status: str | None = None
    auto_replied_at: datetime | None = None

    model_config = {"from_attributes": True}
