from dataclasses import dataclass, field
from decimal import Decimal
from types import SimpleNamespace

from app.services.shop_service import ShopService


class DummyDB:
    def add(self, _obj):
        return None

    def commit(self):
        return None

    def refresh(self, _obj):
        return None


@dataclass
class FakePayment:
    id: int
    payment_no: str
    order_id: int
    method: str
    amount: Decimal
    status: str = "initiated"
    payment_reference: str = ""
    failure_reason: str = ""
    raw_payload: str = ""
    paid_at: object | None = None


@dataclass
class FakeOrder:
    id: int
    order_no: str
    user_id: int
    status: str = "created"
    payment_status: str = "pending"
    shipping_status: str = "pending"
    coupon_code: str | None = None
    points_used: int = 0
    total_amount: Decimal = Decimal("100")
    paid_at: object | None = None
    items: list = field(default_factory=list)
    payments: list = field(default_factory=list)


class FakeRepo:
    def __init__(self) -> None:
        self.db = DummyDB()
        self.user = SimpleNamespace(id=1, points_balance=10)
        self.product = SimpleNamespace(id=11, name="Crystal", stock=10, status="active")
        self.order = FakeOrder(
            id=100,
            order_no="ORD-TEST",
            user_id=1,
            items=[SimpleNamespace(product_id=11, quantity=1)],
            total_amount=Decimal("99.00"),
        )
        self._payment_seq = 1

    def get_order(self, order_id: int):
        return self.order if order_id == self.order.id else None

    def lock_products_by_ids(self, product_ids: list[int]):
        if self.product.id in product_ids:
            return [self.product]
        return []

    def create_payment_attempt(
        self,
        *,
        payment_no: str,
        order_id: int,
        method: str,
        amount: Decimal,
        payment_reference: str,
        raw_payload: str,
    ):
        payment = FakePayment(
            id=self._payment_seq,
            payment_no=payment_no,
            order_id=order_id,
            method=method,
            amount=amount,
            payment_reference=payment_reference,
            raw_payload=raw_payload,
        )
        self._payment_seq += 1
        self.order.payments.insert(0, payment)
        return payment

    def mark_payment_failed(self, payment: FakePayment, reason: str):
        payment.status = "failed"
        payment.failure_reason = reason
        return payment

    def mark_payment_succeeded(self, payment: FakePayment):
        payment.status = "succeeded"
        return payment

    def add_behavior_event(self, *, user_id: int, product_id: int, event_type: str, weight: int = 1):
        return None

    def get_user(self, user_id: int):
        return self.user if user_id == 1 else None

    def get_coupon_by_code(self, code: str):
        return None

    def add_shipment_request(self, *, order_id: int, payload: str):
        return None


def test_pay_order_marks_failed_when_simulated_failure() -> None:
    repo = FakeRepo()
    service = ShopService(repo)  # type: ignore[arg-type]

    paid = service.pay_order(
        order_id=repo.order.id,
        payment_reference="PAY-FAIL-1",
        payment_method="wechat_pay",
        simulate_failure=True,
    )

    assert paid.payment_status == "failed"
    assert paid.status == "created"
    assert paid.payments[0].status == "failed"
    assert "Simulated payment failure" in paid.payments[0].failure_reason


def test_pay_order_marks_success_and_deducts_stock() -> None:
    repo = FakeRepo()
    service = ShopService(repo)  # type: ignore[arg-type]
    service._trigger_low_stock_flow = lambda _product: None  # type: ignore[method-assign]

    paid = service.pay_order(
        order_id=repo.order.id,
        payment_reference="PAY-SUCCESS-1",
        payment_method="alipay",
        simulate_failure=False,
    )

    assert paid.payment_status == "paid"
    assert paid.status == "fulfilled"
    assert paid.shipping_status == "requested"
    assert paid.payments[0].status == "succeeded"
    assert repo.product.stock == 9
