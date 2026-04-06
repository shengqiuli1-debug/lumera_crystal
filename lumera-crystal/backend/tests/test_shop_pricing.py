from decimal import Decimal
from types import SimpleNamespace

from app.services.shop_service import calculate_order_pricing


def test_calculate_order_pricing_with_percent_coupon_and_points() -> None:
    coupon = SimpleNamespace(
        is_active=True,
        min_order_amount=Decimal("50"),
        discount_type="percent",
        discount_value=Decimal("10"),
    )
    result = calculate_order_pricing(
        subtotal=Decimal("200"),
        coupon=coupon,
        points_to_use=30,
        user_points_balance=100,
    )
    # 10% off = 20, plus points 30/10=3 => total discount 23
    assert result.subtotal == Decimal("200.00")
    assert result.discount == Decimal("23.00")
    assert result.total == Decimal("177.00")
    assert result.points_used == 30


def test_calculate_order_pricing_caps_points_by_balance() -> None:
    result = calculate_order_pricing(
        subtotal=Decimal("12"),
        coupon=None,
        points_to_use=500,
        user_points_balance=20,
    )
    assert result.points_used == 20
    assert result.discount == Decimal("2.00")
    assert result.total == Decimal("10.00")
