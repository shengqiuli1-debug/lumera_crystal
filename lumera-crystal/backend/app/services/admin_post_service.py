from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.repositories.admin_post_repository import AdminPostRepository


class AdminPostService:
    def __init__(self, repo: AdminPostRepository) -> None:
        self.repo = repo

    def list_posts(self, **kwargs):
        return self.repo.list(**kwargs)

    def get_or_404(self, post_id: int):
        item = self.repo.get(post_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
        return item

    def create_post(self, payload: dict):
        if self.repo.get_by_slug(payload["slug"]):
            raise HTTPException(status_code=400, detail="Slug already exists")
        if payload.get("status") == "published" and not payload.get("published_at"):
            payload["published_at"] = datetime.now(timezone.utc)
        return self.repo.create(payload)

    def update_post(self, post_id: int, payload: dict):
        item = self.get_or_404(post_id)
        if "slug" in payload and payload["slug"] != item.slug and self.repo.get_by_slug(payload["slug"]):
            raise HTTPException(status_code=400, detail="Slug already exists")
        if payload.get("status") == "published" and not payload.get("published_at") and not item.published_at:
            payload["published_at"] = datetime.now(timezone.utc)
        return self.repo.update(item, payload)

    def delete_post(self, post_id: int) -> None:
        item = self.get_or_404(post_id)
        self.repo.delete(item)
