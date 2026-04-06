from app.services.storage.base import StorageService, StoredMedia


class DatabaseStorageService(StorageService):
    def save_image(
        self,
        *,
        file_name: str,
        original_file_name: str,
        mime_type: str,
        media_kind: str,
        content: bytes,
        sha256: str,
        duration_seconds: float | None = None,
    ) -> StoredMedia:
        return StoredMedia(
            file_name=file_name,
            original_file_name=original_file_name,
            mime_type=mime_type,
            media_kind=media_kind,
            file_size=len(content),
            sha256=sha256,
            storage_type="db",
            binary_data=content,
            duration_seconds=duration_seconds,
        )


class LocalFileStorageService(StorageService):
    def save_image(self, **kwargs) -> StoredMedia:  # type: ignore[override]
        raise NotImplementedError("Local file storage is reserved for future migration")


class S3StorageService(StorageService):
    def save_image(self, **kwargs) -> StoredMedia:  # type: ignore[override]
        raise NotImplementedError("S3 storage is reserved for future migration")
