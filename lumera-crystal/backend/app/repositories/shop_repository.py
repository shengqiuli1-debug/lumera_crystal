from datetime import datetime
from decimal import Decimal

from sqlalchemy import and_, desc, func, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Coupon,
    InventoryAlert,
    Product,
    RestockRequest,
    ShipmentRequest,
    ShopOrder,
    ShopOrderItem,
    ShopPayment,
    ShopUser,
    UserBehaviorEvent,
)


class ShopRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_user(self, user_id: int) -> ShopUser | None:
        return self.db.get(ShopUser, user_id)

    def get_user_by_email(self, email: str) -> ShopUser | None:
        return self.db.scalar(select(ShopUser).where(ShopUser.email == email))

    def create_user(self, *, email: str, name: str) -> ShopUser:
        item = ShopUser(email=email, name=name)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def get_coupon_by_code(self, code: str) -> Coupon | None:
        return self.db.scalar(select(Coupon).where(Coupon.code == code))

    def list_products_with_stock(self, *, page: int, page_size: int) -> tuple[list[Product], int]:
        where_clause = Product.status.in_(["active", "archived"])
        total = self.db.scalar(select(func.count()).select_from(Product).where(where_clause)) or 0
        items = list(
            self.db.scalars(
                select(Product)
                .where(where_clause)
                .order_by(desc(Product.updated_at))
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        return items, total

    def get_product_by_id(self, product_id: int) -> Product | None:
        return self.db.get(Product, product_id)

    def lock_products_by_ids(self, product_ids: list[int]) -> list[Product]:
        return list(self.db.scalars(select(Product).where(Product.id.in_(product_ids)).with_for_update()))

    def create_order(
        self,
        *,
        order_no: str,
        user_id: int,
        shipping_address: str,
        coupon_code: str | None,
        points_used: int,
        subtotal_amount: Decimal,
        discount_amount: Decimal,
        total_amount: Decimal,
        items: list[dict],
    ) -> ShopOrder:
        order = ShopOrder(
            order_no=order_no,
            user_id=user_id,
            shipping_address=shipping_address,
            coupon_code=coupon_code,
            points_used=points_used,
            subtotal_amount=subtotal_amount,
            discount_amount=discount_amount,
            total_amount=total_amount,
        )
        self.db.add(order)
        self.db.flush()
        self.db.add_all(
            [
                ShopOrderItem(
                    order_id=order.id,
                    product_id=item["product_id"],
                    quantity=item["quantity"],
                    unit_price=item["unit_price"],
                    line_total=item["line_total"],
                )
                for item in items
            ]
        )
        self.db.commit()
        return self.get_order(order.id) or order

    def list_orders_by_user(self, *, user_id: int, page: int, page_size: int) -> tuple[list[ShopOrder], int]:
        where_clause = ShopOrder.user_id == user_id
        total = self.db.scalar(select(func.count()).select_from(ShopOrder).where(where_clause)) or 0
        stmt = (
            select(ShopOrder)
            .options(selectinload(ShopOrder.items), selectinload(ShopOrder.payments))
            .where(where_clause)
            .order_by(desc(ShopOrder.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.db.scalars(stmt)), total

    def get_order(self, order_id: int) -> ShopOrder | None:
        return self.db.scalar(
            select(ShopOrder)
            .options(selectinload(ShopOrder.items), selectinload(ShopOrder.payments))
            .where(ShopOrder.id == order_id)
        )

    def create_payment_attempt(
        self,
        *,
        payment_no: str,
        order_id: int,
        method: str,
        amount: Decimal,
        payment_reference: str,
        raw_payload: str,
    ) -> ShopPayment:
        item = ShopPayment(
            payment_no=payment_no,
            order_id=order_id,
            method=method,
            amount=amount,
            status="initiated",
            payment_reference=payment_reference,
            raw_payload=raw_payload,
        )
        self.db.add(item)
        self.db.flush()
        return item

    def mark_payment_succeeded(self, payment: ShopPayment) -> ShopPayment:
        payment.status = "succeeded"
        payment.failure_reason = ""
        payment.paid_at = datetime.utcnow()
        self.db.add(payment)
        self.db.flush()
        return payment

    def mark_payment_failed(self, payment: ShopPayment, reason: str) -> ShopPayment:
        payment.status = "failed"
        payment.failure_reason = reason[:255]
        self.db.add(payment)
        self.db.flush()
        return payment

    def list_payments_by_order(self, *, order_id: int) -> list[ShopPayment]:
        stmt = select(ShopPayment).where(ShopPayment.order_id == order_id).order_by(desc(ShopPayment.created_at))
        return list(self.db.scalars(stmt))

    def add_shipment_request(self, *, order_id: int, payload: str) -> ShipmentRequest:
        request = ShipmentRequest(order_id=order_id, status="requested", payload=payload)
        self.db.add(request)
        self.db.flush()
        return request

    def get_open_alert(self, *, product_id: int) -> InventoryAlert | None:
        return self.db.scalar(
            select(InventoryAlert).where(InventoryAlert.product_id == product_id, InventoryAlert.status == "open")
        )

    def create_alert(self, *, product_id: int, threshold: int, stock_snapshot: int, message: str) -> InventoryAlert:
        item = InventoryAlert(
            product_id=product_id,
            threshold=threshold,
            stock_snapshot=stock_snapshot,
            status="open",
            message=message,
        )
        self.db.add(item)
        self.db.flush()
        return item

    def resolve_alert(self, item: InventoryAlert) -> InventoryAlert:
        item.status = "resolved"
        item.resolved_at = datetime.utcnow()
        self.db.add(item)
        self.db.flush()
        return item

    def get_pending_restock_request(self, *, product_id: int) -> RestockRequest | None:
        return self.db.scalar(
            select(RestockRequest).where(
                RestockRequest.product_id == product_id,
                RestockRequest.status.in_(["pending", "requested"]),
            )
        )

    def create_restock_request(
        self,
        *,
        product_id: int,
        requested_quantity: int,
        status: str,
        external_ref: str,
        provider_response: str,
    ) -> RestockRequest:
        item = RestockRequest(
            product_id=product_id,
            requested_quantity=requested_quantity,
            status=status,
            external_ref=external_ref,
            provider_response=provider_response,
        )
        self.db.add(item)
        self.db.flush()
        return item

    def get_restock_request(self, request_id: int) -> RestockRequest | None:
        return self.db.get(RestockRequest, request_id)

    def add_behavior_event(self, *, user_id: int, product_id: int, event_type: str, weight: int = 1) -> None:
        self.db.add(UserBehaviorEvent(user_id=user_id, product_id=product_id, event_type=event_type, weight=weight))
        self.db.flush()

    def top_behavior_products(self, *, user_id: int, limit: int = 10) -> list[tuple[int, int]]:
        stmt = (
            select(UserBehaviorEvent.product_id, func.sum(UserBehaviorEvent.weight).label("score"))
            .where(UserBehaviorEvent.user_id == user_id)
            .group_by(UserBehaviorEvent.product_id)
            .order_by(desc("score"))
            .limit(limit)
        )
        return [(product_id, int(score)) for product_id, score in self.db.execute(stmt).all()]

    def paid_orders_between(self, *, from_date: datetime, to_date: datetime) -> tuple[int, Decimal]:
        stmt = select(func.count(ShopOrder.id), func.coalesce(func.sum(ShopOrder.total_amount), 0)).where(
            and_(
                ShopOrder.payment_status == "paid",
                ShopOrder.paid_at.is_not(None),
                ShopOrder.paid_at >= from_date,
                ShopOrder.paid_at < to_date,
            )
        )
        count, total = self.db.execute(stmt).one()
        return int(count or 0), Decimal(total or 0)

    def low_stock_product_count(self, threshold: int) -> int:
        return int(self.db.scalar(select(func.count(Product.id)).where(Product.stock < threshold)) or 0)

    def total_product_count(self) -> int:
        return int(self.db.scalar(select(func.count(Product.id))) or 0)
