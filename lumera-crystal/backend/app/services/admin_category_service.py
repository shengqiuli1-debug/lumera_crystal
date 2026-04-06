from fastapi import HTTPException, status

from app.repositories.admin_category_repository import AdminCategoryRepository


class AdminCategoryService:
    def __init__(self, repo: AdminCategoryRepository) -> None:
        self.repo = repo

    def list_categories(self, *, search: str | None = None):
        return self.repo.list(search=search)

    def get_or_404(self, category_id: int):
        item = self.repo.get(category_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        return item

    def create_category(self, payload: dict):
        if self.repo.get_by_slug(payload["slug"]):
            raise HTTPException(status_code=400, detail="Slug already exists")
        return self.repo.create(payload)

    def update_category(self, category_id: int, payload: dict):
        item = self.get_or_404(category_id)
        if "slug" in payload and payload["slug"] != item.slug and self.repo.get_by_slug(payload["slug"]):
            raise HTTPException(status_code=400, detail="Slug already exists")
        return self.repo.update(item, payload)

    def delete_category(self, category_id: int):
        item = self.get_or_404(category_id)
        if self.repo.count_products(category_id) > 0:
            raise HTTPException(status_code=400, detail="Category has products and cannot be deleted")
        self.repo.delete(item)
