import hashlib
import re
import unicodedata

from fastapi import HTTPException, status

from app.core.config import settings
from app.models import MediaAsset
from app.repositories.media_repository import MediaRepository
from app.schemas.media import MediaAssetRead
from app.services.media_processing import trim_gif, trim_video
from app.services.storage.base import StorageService

_EXT_BY_MIME = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "video/mp4": ".mp4",
    "video/webm": ".webm",
    "video/quicktime": ".mov",
}


def _guess_magic_mime(content: bytes) -> str | None:
    if content.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "image/webp"
    if content.startswith(b"GIF87a") or content.startswith(b"GIF89a"):
        return "image/gif"
    if len(content) >= 12 and content[4:8] == b"ftyp":
        brand = content[8:12]
        if brand in {b"isom", b"iso2", b"avc1", b"mp41", b"mp42"}:
            return "video/mp4"
        if brand in {b"qt  "}:
            return "video/quicktime"
    if len(content) >= 12 and content[:4] == b"\x1a\x45\xdf\xa3":
        return "video/webm"
    return None


def _media_kind_by_mime(mime_type: str) -> str:
    if mime_type.startswith("video/"):
        return "video"
    if mime_type == "image/gif":
        return "animation"
    return "image"


def _normalize_filename(original_name: str, mime_type: str) -> str:
    base = unicodedata.normalize("NFKD", original_name or "image").encode("ascii", "ignore").decode("ascii")
    base = re.sub(r"[^a-zA-Z0-9._-]+", "-", base).strip("-._")
    if not base:
        base = "image"
    if "." in base:
        base = base.rsplit(".", 1)[0]
    return f"{base[:100]}-{hashlib.sha1(original_name.encode('utf-8', 'ignore')).hexdigest()[:10]}{_EXT_BY_MIME[mime_type]}"


def build_media_url(media_id: int) -> str:
    return f"{settings.app_public_base_url.rstrip('/')}/api/v1/media/{media_id}"


def to_media_read(media: MediaAsset) -> MediaAssetRead:
    return MediaAssetRead(
        id=media.id,
        url=build_media_url(media.id),
        file_name=media.file_name,
        mime_type=media.mime_type,
        media_kind=media.media_kind,
        file_size=media.file_size,
        duration_seconds=media.duration_seconds,
        alt_text=media.alt_text,
        width=media.width,
        height=media.height,
        created_at=media.created_at,
    )


class MediaService:
    def __init__(self, repo: MediaRepository, storage: StorageService) -> None:
        self.repo = repo
        self.storage = storage

    def validate_upload(self, *, content: bytes, mime_type: str | None, original_name: str) -> tuple[str, str, str]:
        if not mime_type:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing content type")
        if mime_type not in settings.allowed_media_mime_types:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported mime type: {mime_type}")
        if len(content) == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")

        is_video_or_animation = bool(mime_type.startswith("video/") or mime_type == "image/gif")
        max_size_mb = settings.media_max_video_upload_size_mb if is_video_or_animation else settings.media_max_upload_size_mb
        max_size = max_size_mb * 1024 * 1024
        if len(content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large, max {max_size_mb}MB",
            )

        magic_mime = _guess_magic_mime(content)
        if magic_mime is None or magic_mime != mime_type:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Illegal or mismatched media content")

        sha256 = hashlib.sha256(content).hexdigest()
        normalized = _normalize_filename(original_name, mime_type)
        return normalized, sha256, magic_mime

    def _normalize_media_content(self, *, content: bytes, mime_type: str) -> tuple[bytes, str, float | None]:
        max_seconds = settings.media_max_duration_seconds
        if mime_type == "image/gif":
            try:
                processed, duration = trim_gif(content, max_seconds)
            except Exception as exc:  # noqa: BLE001
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid GIF content: {exc}") from exc
            return processed, mime_type, duration
        if mime_type.startswith("video/"):
            try:
                processed, duration, normalized_mime = trim_video(content, mime_type, max_seconds)
            except Exception as exc:  # noqa: BLE001
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid video content: {exc}") from exc
            return processed, normalized_mime, duration
        return content, mime_type, None

    def save_uploaded_media(self, *, content: bytes, mime_type: str, original_name: str) -> MediaAsset:
        _, _, validated_mime = self.validate_upload(content=content, mime_type=mime_type, original_name=original_name)
        normalized_content, normalized_mime, duration_seconds = self._normalize_media_content(
            content=content, mime_type=validated_mime
        )
        file_name = _normalize_filename(original_name, normalized_mime)
        sha256 = hashlib.sha256(normalized_content).hexdigest()

        exists = self.repo.get_by_sha256_and_size(
            sha256=sha256,
            file_size=len(normalized_content),
            mime_type=normalized_mime,
        )
        if exists:
            return exists

        stored = self.storage.save_image(
            file_name=file_name,
            original_file_name=original_name,
            mime_type=normalized_mime,
            media_kind=_media_kind_by_mime(normalized_mime),
            content=normalized_content,
            sha256=sha256,
            duration_seconds=duration_seconds,
        )
        return self.repo.create(
            {
                "biz_type": "unbound",
                "biz_id": None,
                "file_name": stored.file_name,
                "original_file_name": stored.original_file_name,
                "mime_type": stored.mime_type,
                "media_kind": stored.media_kind,
                "file_size": stored.file_size,
                "sha256": stored.sha256,
                "storage_type": stored.storage_type,
                "binary_data": stored.binary_data,
                "duration_seconds": stored.duration_seconds,
                "width": stored.width,
                "height": stored.height,
                "alt_text": stored.alt_text,
            }
        )

    def get_or_404(self, media_id: int) -> MediaAsset:
        item = self.repo.get(media_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found")
        return item

    def bind_media(self, media_ids: list[int], *, biz_type: str, biz_id: int) -> None:
        for media_id in media_ids:
            media = self.repo.get(media_id)
            if media:
                self.repo.mark_bound(media, biz_type=biz_type, biz_id=biz_id)
