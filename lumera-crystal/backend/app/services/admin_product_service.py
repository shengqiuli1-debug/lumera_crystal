from fastapi import HTTPException, status

from app.repositories.admin_category_repository import AdminCategoryRepository
from app.repositories.admin_product_repository import AdminProductRepository
from app.repositories.media_repository import MediaRepository
from app.services.media_service import MediaService


class AdminProductService:
    def __init__(
        self,
        repo: AdminProductRepository,
        category_repo: AdminCategoryRepository,
        media_repo: MediaRepository,
        media_service: MediaService,
    ) -> None:
        self.repo = repo
        self.category_repo = category_repo
        self.media_repo = media_repo
        self.media_service = media_service

    def list_products(self, **kwargs):
        return self.repo.list(**kwargs)

    def get_or_404(self, product_id: int):
        item = self.repo.get(product_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        return item

    def create_product(self, payload: dict):
        gallery_media_ids = payload.pop("gallery_media_ids", [])
        if self.repo.get_by_slug(payload["slug"]):
            raise HTTPException(status_code=400, detail="Slug already exists")
        if not self.category_repo.get(payload["category_id"]):
            raise HTTPException(status_code=400, detail="Category not found")
        cover_media_id = payload.get("cover_media_id")
        if cover_media_id is not None and not self.media_repo.get(cover_media_id):
            raise HTTPException(status_code=400, detail="Cover media not found")
        for media_id in gallery_media_ids:
            if not self.media_repo.get(media_id):
                raise HTTPException(status_code=400, detail=f"Gallery media not found: {media_id}")

        item = self.repo.create(payload, gallery_media_ids=gallery_media_ids)
        bind_ids = [media_id for media_id in [cover_media_id, *gallery_media_ids] if media_id]
        self.media_service.bind_media(bind_ids, biz_type="product", biz_id=item.id)
        return item

    def update_product(self, product_id: int, payload: dict):
        gallery_media_ids = payload.pop("gallery_media_ids", None)
        item = self.get_or_404(product_id)
        if "slug" in payload and payload["slug"] != item.slug and self.repo.get_by_slug(payload["slug"]):
            raise HTTPException(status_code=400, detail="Slug already exists")
        if "category_id" in payload and not self.category_repo.get(payload["category_id"]):
            raise HTTPException(status_code=400, detail="Category not found")
        cover_media_id = payload.get("cover_media_id")
        if cover_media_id is not None and not self.media_repo.get(cover_media_id):
            raise HTTPException(status_code=400, detail="Cover media not found")
        if gallery_media_ids is not None:
            for media_id in gallery_media_ids:
                if not self.media_repo.get(media_id):
                    raise HTTPException(status_code=400, detail=f"Gallery media not found: {media_id}")

        updated = self.repo.update(item, payload, gallery_media_ids=gallery_media_ids)
        bind_ids = []
        if cover_media_id:
            bind_ids.append(cover_media_id)
        if gallery_media_ids:
            bind_ids.extend(gallery_media_ids)
        if bind_ids:
            self.media_service.bind_media(bind_ids, biz_type="product", biz_id=updated.id)
        return updated

    def delete_product(self, product_id: int) -> None:
        item = self.get_or_404(product_id)
        self.repo.delete(item)

    def bulk_update_status(self, ids: list[int], status: str) -> int:
        return self.repo.bulk_update_status(ids, status)
