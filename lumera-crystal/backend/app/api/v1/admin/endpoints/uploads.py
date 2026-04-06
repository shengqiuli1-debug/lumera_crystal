from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models import AdminUser
from app.repositories.media_repository import MediaRepository
from app.schemas.media import MediaUploadResponse
from app.services.media_service import MediaService, to_media_read
from app.services.storage.db_storage import DatabaseStorageService

router = APIRouter(prefix="/uploads", tags=["admin-uploads"])


@router.post("/images", response_model=MediaUploadResponse)
async def upload_images(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> MediaUploadResponse:
    repo = MediaRepository(db)
    service = MediaService(repo, DatabaseStorageService())
    items = []
    for file in files:
        content = await file.read()
        media = service.save_uploaded_media(
            content=content,
            mime_type=file.content_type or "",
            original_name=file.filename or "media",
        )
        items.append(to_media_read(media))
    return MediaUploadResponse(items=items)


@router.post("/image")
async def upload_single_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> dict:
    repo = MediaRepository(db)
    service = MediaService(repo, DatabaseStorageService())
    content = await file.read()
    media = service.save_uploaded_media(
        content=content,
        mime_type=file.content_type or "",
        original_name=file.filename or "media",
    )
    item = to_media_read(media)
    return {
        "id": item.id,
        "url": item.url,
        "file_name": item.file_name,
        "mime_type": item.mime_type,
        "media_kind": item.media_kind,
        "file_size": item.file_size,
        "duration_seconds": item.duration_seconds,
    }
