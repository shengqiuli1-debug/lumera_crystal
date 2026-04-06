from datetime import datetime

from pydantic import BaseModel


class MediaAssetRead(BaseModel):
    id: int
    url: str
    file_name: str
    mime_type: str
    media_kind: str
    file_size: int
    duration_seconds: float | None = None
    alt_text: str | None = None
    width: int | None = None
    height: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MediaUploadResponse(BaseModel):
    items: list[MediaAssetRead]
