from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import MediaAsset


class MediaRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, media_id: int) -> MediaAsset | None:
        return self.db.get(MediaAsset, media_id)

    def get_by_sha256_and_size(self, *, sha256: str, file_size: int, mime_type: str) -> MediaAsset | None:
        stmt = select(MediaAsset).where(
            MediaAsset.sha256 == sha256,
            MediaAsset.file_size == file_size,
            MediaAsset.mime_type == mime_type,
            MediaAsset.storage_type == "db",
        )
        return self.db.scalar(stmt)

    def create(self, payload: dict) -> MediaAsset:
        item = MediaAsset(**payload)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def mark_bound(self, item: MediaAsset, *, biz_type: str, biz_id: int) -> MediaAsset:
        item.biz_type = biz_type
        item.biz_id = biz_id
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item
