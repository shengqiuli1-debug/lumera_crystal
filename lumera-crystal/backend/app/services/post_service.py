from app.repositories.post_repository import PostRepository


class PostService:
    def __init__(self, repo: PostRepository) -> None:
        self.repo = repo

    def list_posts(self, page: int, page_size: int, search: str | None):
        return self.repo.list(page, page_size, search)

    def get_post_by_slug(self, slug: str):
        return self.repo.get_by_slug(slug)
