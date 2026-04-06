from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.media_repository import MediaRepository
from app.services.media_service import MediaService
from app.services.storage.db_storage import DatabaseStorageService

router = APIRouter(prefix="/media", tags=["media"])


@router.get("/{media_id}")
def get_media(media_id: int, db: Session = Depends(get_db)) -> Response:
    service = MediaService(MediaRepository(db), DatabaseStorageService())
    media = service.get_or_404(media_id)
    headers = {
        "Cache-Control": "public, max-age=86400",
        "ETag": media.sha256,
    }
    return Response(content=media.binary_data, media_type=media.mime_type, headers=headers)
