import uuid
from pathlib import Path

from fastapi import UploadFile


class AdminUploadService:
    def __init__(self, *, upload_root: Path, public_base_url: str) -> None:
        self.upload_root = upload_root
        self.public_base_url = public_base_url.rstrip("/")

    async def save_image(self, file: UploadFile) -> dict[str, str]:
        suffix = Path(file.filename or "").suffix.lower() or ".jpg"
        folder = self.upload_root / "images"
        folder.mkdir(parents=True, exist_ok=True)
        filename = f"{uuid.uuid4().hex}{suffix}"
        file_path = folder / filename

        content = await file.read()
        file_path.write_bytes(content)
        relative_path = f"/uploads/images/{filename}"
        return {"url": f"{self.public_base_url}{relative_path}", "path": relative_path}
