from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class StoredMedia:
    file_name: str
    original_file_name: str
    mime_type: str
    media_kind: str
    file_size: int
    sha256: str
    storage_type: str
    binary_data: bytes
    duration_seconds: float | None = None
    width: int | None = None
    height: int | None = None
    alt_text: str | None = None


class StorageService(ABC):
    @abstractmethod
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
        raise NotImplementedError
