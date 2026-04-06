from types import SimpleNamespace

from app.services.shop_service import ShopService


class FakeRepo:
    def __init__(self) -> None:
        self._users = {1: SimpleNamespace(id=1)}
        self._products = {
            10: SimpleNamespace(id=10, status="active"),
            11: SimpleNamespace(id=11, status="active"),
            12: SimpleNamespace(id=12, status="archived"),
        }

    def get_user(self, user_id: int):
        return self._users.get(user_id)

    def top_behavior_products(self, *, user_id: int, limit: int = 10):
        return [(12, 50), (11, 20), (10, 10)]

    def lock_products_by_ids(self, product_ids: list[int]):
        return [self._products[item] for item in product_ids if item in self._products]

    def list_products_with_stock(self, *, page: int, page_size: int):
        return [self._products[10], self._products[11]], 2


def test_recommendation_filters_out_archived_products() -> None:
    service = ShopService(FakeRepo())  # type: ignore[arg-type]
    result = service.get_recommendations(user_id=1, limit=2)
    assert result == [(11, 20.0), (10, 10.0)]
