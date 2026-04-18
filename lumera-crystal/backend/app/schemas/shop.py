from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


OrderStatus = Literal["created", "cancelled", "fulfilled"]
PaymentStatus = Literal["pending", "paid", "failed", "refunded"]
ShippingStatus = Literal["pending", "requested", "shipped"]
PaymentMethod = Literal["alipay", "wechat_pay", "bank_card", "mock"]
PaymentAttemptStatus = Literal["initiated", "succeeded", "failed"]


class ShopUserCreate(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=120)


class ShopUserRead(BaseModel):
    id: int
    email: EmailStr
    name: str
    points_balance: int
    is_active: bool

    model_config = {"from_attributes": True}


class CouponRead(BaseModel):
    id: int
    code: str
    discount_type: str
    discount_value: Decimal
    min_order_amount: Decimal
    is_active: bool

    model_config = {"from_attributes": True}


class ShopProductInventoryRead(BaseModel):
    id: int
    slug: str
    name: str
    price: Decimal
    status: str
    stock: int
    low_stock_threshold: int = 5
    low_stock: bool


class ShopProductInventoryListResponse(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[ShopProductInventoryRead]


class ShopOrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(ge=1, le=999)


class ShopOrderCreate(BaseModel):
    user_id: int
    items: list[ShopOrderItemCreate] = Field(min_length=1)
    shipping_address: str = Field(min_length=5, max_length=300)
    coupon_code: str | None = None
    points_to_use: int = Field(default=0, ge=0)


class ShopOrderUpdate(BaseModel):
    shipping_address: str | None = Field(default=None, min_length=5, max_length=300)
    status: OrderStatus | None = None


class ShopOrderItemRead(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    line_total: Decimal

    model_config = {"from_attributes": True}


class ShopPaymentRead(BaseModel):
    id: int
    payment_no: str
    order_id: int
    method: PaymentMethod
    amount: Decimal
    status: PaymentAttemptStatus
    payment_reference: str
    failure_reason: str
    paid_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ShopOrderRead(BaseModel):
    id: int
    order_no: str
    user_id: int
    status: OrderStatus
    payment_status: PaymentStatus
    shipping_status: ShippingStatus
    coupon_code: str | None
    points_used: int
    subtotal_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    paid_at: datetime | None
    shipping_address: str
    created_at: datetime
    updated_at: datetime
    items: list[ShopOrderItemRead]
    payments: list[ShopPaymentRead] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ShopOrderPayRequest(BaseModel):
    payment_reference: str | None = None
    payment_method: PaymentMethod = "mock"
    payer_name: str | None = Field(default=None, max_length=120)
    coupon_code: str | None = Field(default=None, max_length=60)
    simulate_failure: bool = False


class ShopLogisticsEventRead(BaseModel):
    step_code: str
    step_label: str
    detail: str
    occurred_at: datetime


class ShopLogisticsTraceRead(BaseModel):
    trace_no: str
    order_no: str
    order_id: int | None
    carrier: str
    tracking_no: str
    current_step: str
    current_label: str
    created_at: datetime
    updated_at: datetime
    events: list[ShopLogisticsEventRead]


class ShopOrderListResponse(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[ShopOrderRead]


class InventoryAlertRead(BaseModel):
    id: int
    product_id: int
    threshold: int
    stock_snapshot: int
    status: str
    message: str
    resolved_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RestockRequestRead(BaseModel):
    id: int
    product_id: int
    requested_quantity: int
    status: str
    external_ref: str
    provider_response: str
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RestockCompleteRequest(BaseModel):
    quantity: int = Field(ge=1, le=99999)


class RecommendationItem(BaseModel):
    product_id: int
    score: float


class RecommendationResponse(BaseModel):
    user_id: int
    items: list[RecommendationItem]


class ReportSummaryResponse(BaseModel):
    range: Literal["daily", "weekly", "monthly"]
    from_date: datetime
    to_date: datetime
    total_sales_amount: Decimal
    paid_order_count: int
    low_stock_product_count: int
    total_product_count: int
