from app.repositories.category_repository import CategoryRepository


class CategoryService:
    def __init__(self, repo: CategoryRepository) -> None:
        self.repo = repo

    def list_categories(self):
        return self.repo.list()

    def get_by_slug(self, slug: str):
        return self.repo.get_by_slug(slug)
