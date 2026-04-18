from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class ShopUser(TimestampMixin, Base):
    __tablename__ = "shop_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(180), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    points_balance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    orders = relationship("ShopOrder", back_populates="user")


class Coupon(TimestampMixin, Base):
    __tablename__ = "coupons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(60), nullable=False, unique=True, index=True)
    discount_type: Mapped[str] = mapped_column(String(20), nullable=False, default="percent")
    discount_value: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0"))
    min_order_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    usage_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    used_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class ShopOrder(TimestampMixin, Base):
    __tablename__ = "shop_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_no: Mapped[str] = mapped_column(String(40), nullable=False, unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("shop_users.id", ondelete="RESTRICT"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="created", index=True)
    payment_status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending", index=True)
    shipping_status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending", index=True)
    coupon_code: Mapped[str | None] = mapped_column(String(60), nullable=True)
    points_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    subtotal_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0"))
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0"))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    shipping_address: Mapped[str] = mapped_column(Text, nullable=False, default="")

    user = relationship("ShopUser", back_populates="orders")
    items = relationship("ShopOrderItem", back_populates="order", cascade="all, delete-orphan")
    payments = relationship(
        "ShopPayment",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="ShopPayment.created_at.desc()",
    )
    shipment_requests = relationship("ShipmentRequest", back_populates="order", cascade="all, delete-orphan")


class ShopOrderItem(Base):
    __tablename__ = "shop_order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("shop_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0"))
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0"))

    order = relationship("ShopOrder", back_populates="items")
    product = relationship("Product")

    __table_args__ = (UniqueConstraint("order_id", "product_id", name="uq_shop_order_items_order_product"),)


class ShopPayment(TimestampMixin, Base):
    __tablename__ = "shop_payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    payment_no: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("shop_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    method: Mapped[str] = mapped_column(String(30), nullable=False, default="mock")
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0"))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="initiated", index=True)
    payment_reference: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    failure_reason: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    raw_payload: Mapped[str] = mapped_column(Text, nullable=False, default="")
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    order = relationship("ShopOrder", back_populates="payments")


class InventoryAlert(TimestampMixin, Base):
    __tablename__ = "inventory_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    stock_snapshot: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open", index=True)
    message: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    product = relationship("Product")


class RestockRequest(TimestampMixin, Base):
    __tablename__ = "restock_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    requested_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    external_ref: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    provider_response: Mapped[str] = mapped_column(Text, nullable=False, default="")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    product = relationship("Product")


class ShipmentRequest(TimestampMixin, Base):
    __tablename__ = "shipment_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("shop_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    carrier: Mapped[str] = mapped_column(String(80), nullable=False, default="mock-express")
    tracking_no: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    payload: Mapped[str] = mapped_column(Text, nullable=False, default="")

    order = relationship("ShopOrder", back_populates="shipment_requests")


class UserBehaviorEvent(TimestampMixin, Base):
    __tablename__ = "user_behavior_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("shop_users.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    weight: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    user = relationship("ShopUser")
    product = relationship("Product")


Index("ix_shop_orders_user_paid_at", ShopOrder.user_id, ShopOrder.paid_at)
Index("ix_shop_payments_order_created_at", ShopPayment.order_id, ShopPayment.created_at)
Index("ix_restock_requests_product_status", RestockRequest.product_id, RestockRequest.status)
