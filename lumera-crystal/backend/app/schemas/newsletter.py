from pydantic import BaseModel, EmailStr, Field


class NewsletterCreate(BaseModel):
    email: EmailStr
    source: str = Field(default="website", max_length=80)


class NewsletterRead(BaseModel):
    id: int
    email: EmailStr
    source: str

    model_config = {"from_attributes": True}
