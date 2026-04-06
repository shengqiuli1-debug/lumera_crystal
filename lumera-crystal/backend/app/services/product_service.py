from app.repositories.product_repository import ProductRepository


class ProductService:
    def __init__(self, repo: ProductRepository) -> None:
        self.repo = repo

    def list_products(
        self,
        page: int,
        page_size: int,
        *,
        category: str | None,
        min_price: float | None,
        max_price: float | None,
        color: str | None,
        intention: str | None,
        search: str | None,
    ):
        return self.repo.list(
            page,
            page_size,
            category_slug=category,
            min_price=min_price,
            max_price=max_price,
            color=color,
            intention=intention,
            search=search,
        )

    def get_product_by_slug(self, slug: str):
        return self.repo.get_by_slug(slug)
