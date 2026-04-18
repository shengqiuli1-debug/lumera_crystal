from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.repositories.shop_repository import ShopRepository
from app.schemas.shop import (
    RecommendationItem,
    RecommendationResponse,
    ReportSummaryResponse,
    RestockCompleteRequest,
    RestockRequestRead,
    ShopOrderCreate,
    ShopLogisticsTraceRead,
    ShopOrderListResponse,
    ShopPaymentRead,
    ShopOrderPayRequest,
    ShopOrderRead,
    ShopOrderUpdate,
    ShopProductInventoryListResponse,
    ShopProductInventoryRead,
    ShopUserCreate,
    ShopUserRead,
)
from app.services.shop_service import ShopService

router = APIRouter(prefix="/shop", tags=["shop"])


def _service(db: Session) -> ShopService:
    return ShopService(ShopRepository(db))


@router.post("/users", response_model=ShopUserRead, status_code=status.HTTP_201_CREATED)
def create_shop_user(payload: ShopUserCreate, db: Session = Depends(get_db)) -> ShopUserRead:
    return _service(db).create_user(email=payload.email, name=payload.name)


@router.get("/products", response_model=ShopProductInventoryListResponse)
def list_shop_products(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> ShopProductInventoryListResponse:
    items, total = _service(db).list_products_with_stock(page=page, page_size=page_size)
    wrapped: list[ShopProductInventoryRead] = [
        ShopProductInventoryRead(
            id=item.id,
            slug=item.slug,
            name=item.name,
            price=item.price,
            status=item.status,
            stock=item.stock,
            low_stock_threshold=settings.stock_low_threshold,
            low_stock=item.stock < settings.stock_low_threshold,
        )
        for item in items
    ]
    return ShopProductInventoryListResponse(
        page=page,
        page_size=page_size,
        total=total,
        items=wrapped,
    )


@router.get("/products/{product_id}/inventory", response_model=ShopProductInventoryRead)
def get_product_inventory(product_id: int, db: Session = Depends(get_db)) -> ShopProductInventoryRead:
    return ShopProductInventoryRead(**_service(db).get_product_inventory(product_id))


@router.post("/orders", response_model=ShopOrderRead, status_code=status.HTTP_201_CREATED)
def create_order(payload: ShopOrderCreate, db: Session = Depends(get_db)) -> ShopOrderRead:
    created = _service(db).create_order(
        user_id=payload.user_id,
        shipping_address=payload.shipping_address,
        items=[item.model_dump() for item in payload.items],
        coupon_code=payload.coupon_code,
        points_to_use=payload.points_to_use,
    )
    return created


@router.patch("/orders/{order_id}", response_model=ShopOrderRead)
def update_order(order_id: int, payload: ShopOrderUpdate, db: Session = Depends(get_db)) -> ShopOrderRead:
    return _service(db).update_order(order_id, payload.model_dump(exclude_unset=True))


@router.post("/orders/{order_id}/pay", response_model=ShopOrderRead)
def pay_order(order_id: int, payload: ShopOrderPayRequest, db: Session = Depends(get_db)) -> ShopOrderRead:
    return _service(db).pay_order(
        order_id=order_id,
        payment_reference=payload.payment_reference,
        payment_method=payload.payment_method,
        payer_name=payload.payer_name,
        coupon_code=payload.coupon_code,
        simulate_failure=payload.simulate_failure,
    )


@router.get("/orders/{order_id}/payments", response_model=list[ShopPaymentRead])
def list_order_payments(order_id: int, db: Session = Depends(get_db)) -> list[ShopPaymentRead]:
    return _service(db).list_order_payments(order_id=order_id)


@router.get("/orders/{order_id}/logistics", response_model=ShopLogisticsTraceRead)
def get_order_logistics(order_id: int, db: Session = Depends(get_db)) -> ShopLogisticsTraceRead:
    return ShopLogisticsTraceRead(**_service(db).get_order_logistics(order_id=order_id))


@router.get("/users/{user_id}/orders", response_model=ShopOrderListResponse)
def list_user_orders(
    user_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> ShopOrderListResponse:
    items, total = _service(db).list_user_orders(user_id=user_id, page=page, page_size=page_size)
    return ShopOrderListResponse(page=page, page_size=page_size, total=total, items=items)


@router.post("/users/{user_id}/events/view/{product_id}")
def track_product_view(user_id: int, product_id: int, db: Session = Depends(get_db)) -> dict:
    _service(db).record_view(user_id=user_id, product_id=product_id)
    return {"success": True}


@router.get("/users/{user_id}/recommendations", response_model=RecommendationResponse)
def get_user_recommendations(
    user_id: int,
    limit: int = Query(default=8, ge=1, le=20),
    db: Session = Depends(get_db),
) -> RecommendationResponse:
    items = _service(db).get_recommendations(user_id=user_id, limit=limit)
    return RecommendationResponse(
        user_id=user_id,
        items=[RecommendationItem(product_id=product_id, score=score) for product_id, score in items],
    )


@router.get("/reports/summary", response_model=ReportSummaryResponse)
def get_report_summary(
    range: str = Query(default="daily", pattern="^(daily|weekly|monthly)$"),
    db: Session = Depends(get_db),
) -> ReportSummaryResponse:
    return ReportSummaryResponse(**_service(db).report_summary(range_type=range))


@router.post("/inventory/restock-requests/{request_id}/complete", response_model=RestockRequestRead)
def complete_restock_request(
    request_id: int,
    payload: RestockCompleteRequest,
    db: Session = Depends(get_db),
) -> RestockRequestRead:
    return _service(db).complete_restock(request_id=request_id, quantity=payload.quantity)
