from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.exc import ProgrammingError

from app.core.config import settings
from app.models import Coupon, Product, ShopOrder
from app.repositories.shop_repository import ShopRepository
from app.services.email_service import EmailService
from app.services.supplier_service import SupplierService

MONEY = Decimal("0.01")


def money(value: Decimal | int | float | str) -> Decimal:
    return Decimal(value).quantize(MONEY, rounding=ROUND_HALF_UP)


@dataclass
class PricingResult:
    subtotal: Decimal
    discount: Decimal
    total: Decimal
    points_used: int


def calculate_order_pricing(
    *,
    subtotal: Decimal,
    coupon: Coupon | None,
    points_to_use: int,
    user_points_balance: int,
) -> PricingResult:
    subtotal = money(subtotal)
    discount = Decimal("0")
    if coupon and coupon.is_active and subtotal >= money(coupon.min_order_amount):
        if coupon.discount_type == "fixed":
            discount += min(subtotal, money(coupon.discount_value))
        else:
            percent = min(Decimal("100"), max(Decimal("0"), Decimal(coupon.discount_value)))
            discount += money(subtotal * (percent / Decimal("100")))

    allowed_points = min(max(points_to_use, 0), max(user_points_balance, 0))
    points_discount = money(Decimal(allowed_points) / Decimal(settings.points_earn_rate))
    if points_discount > subtotal - discount:
        points_discount = max(Decimal("0"), subtotal - discount)
        allowed_points = int((points_discount * Decimal(settings.points_earn_rate)).to_integral_value())

    discount += points_discount
    total = max(Decimal("0"), subtotal - discount)
    return PricingResult(
        subtotal=money(subtotal),
        discount=money(discount),
        total=money(total),
        points_used=allowed_points,
    )


class ShopService:
    def __init__(
        self,
        repo: ShopRepository,
        email_service: EmailService | None = None,
        supplier_service: SupplierService | None = None,
    ) -> None:
        self.repo = repo
        self.email_service = email_service or EmailService()
        self.supplier_service = supplier_service or SupplierService()

    def create_user(self, *, email: str, name: str):
        exists = self.repo.get_user_by_email(email)
        if exists:
            if name and name.strip() and exists.name != name.strip():
                exists.name = name.strip()
                self.repo.db.add(exists)
                self.repo.db.commit()
                self.repo.db.refresh(exists)
            return exists
        return self.repo.create_user(email=email, name=name)

    def list_products_with_stock(self, *, page: int, page_size: int):
        return self.repo.list_products_with_stock(page=page, page_size=page_size)

    def get_product_inventory(self, product_id: int):
        product = self.repo.get_product_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        threshold = settings.stock_low_threshold
        return {
            "id": product.id,
            "slug": product.slug,
            "name": product.name,
            "price": product.price,
            "status": product.status,
            "stock": product.stock,
            "low_stock_threshold": threshold,
            "low_stock": product.stock < threshold,
        }

    def _assert_coupon_valid(self, coupon: Coupon | None) -> Coupon | None:
        if not coupon:
            return None
        now = datetime.now(timezone.utc)
        if not coupon.is_active:
            raise HTTPException(status_code=400, detail="Coupon is inactive")
        if coupon.start_at and coupon.start_at > now:
            raise HTTPException(status_code=400, detail="Coupon is not started")
        if coupon.end_at and coupon.end_at < now:
            raise HTTPException(status_code=400, detail="Coupon is expired")
        if coupon.usage_limit is not None and coupon.used_count >= coupon.usage_limit:
            raise HTTPException(status_code=400, detail="Coupon usage limit reached")
        return coupon

    def _order_no(self) -> str:
        return f"ORD-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}"

    def _payment_no(self) -> str:
        return f"PAY-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid4().hex[:10].upper()}"

    def _call_logistics(self, *, method: str, path: str, payload: dict | None = None) -> dict:
        base = settings.logistics_service_base_url.rstrip("/") + "/"
        url = urljoin(base, path.lstrip("/"))
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(
            url,
            data=body,
            method=method.upper(),
            headers={"Content-Type": "application/json"} if body is not None else {},
        )
        try:
            with urlopen(request, timeout=settings.logistics_service_timeout_seconds) as response:
                raw = response.read().decode("utf-8") if response.readable() else ""
                return json.loads(raw) if raw else {}
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise HTTPException(status_code=exc.code, detail=detail or "Logistics service error") from exc
        except URLError as exc:
            raise HTTPException(status_code=503, detail=f"Logistics service unavailable: {exc.reason}") from exc

    def _ensure_logistics_trace(self, order: ShopOrder) -> None:
        if not settings.logistics_service_enabled:
            return
        payload = {
            "order_no": order.order_no,
            "order_id": order.id,
            "carrier": "mock-express",
            "tracking_no": f"TRK-{order.order_no}",
        }
        try:
            self._call_logistics(method="POST", path="/traces", payload=payload)
        except HTTPException:
            # Do not fail payment flow if logistics service is temporarily unavailable.
            pass

    def create_order(
        self,
        *,
        user_id: int,
        shipping_address: str,
        items: list[dict],
        coupon_code: str | None,
        points_to_use: int,
    ):
        user = self.repo.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        product_ids = [item["product_id"] for item in items]
        products = {item.id: item for item in self.repo.lock_products_by_ids(product_ids)}
        if len(products) != len(set(product_ids)):
            raise HTTPException(status_code=400, detail="Some products do not exist")

        order_items = []
        subtotal = Decimal("0")
        for item in items:
            product = products[item["product_id"]]
            quantity = int(item["quantity"])
            if product.status != "active":
                raise HTTPException(status_code=400, detail=f"Product is not on shelf: {product.name}")
            if product.stock < quantity:
                raise HTTPException(status_code=400, detail=f"Insufficient stock: {product.name}")
            unit_price = money(product.price)
            line_total = money(unit_price * quantity)
            subtotal += line_total
            order_items.append(
                {
                    "product_id": product.id,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "line_total": line_total,
                }
            )

        coupon = self._assert_coupon_valid(self.repo.get_coupon_by_code(coupon_code)) if coupon_code else None
        pricing = calculate_order_pricing(
            subtotal=subtotal,
            coupon=coupon,
            points_to_use=points_to_use,
            user_points_balance=user.points_balance,
        )
        return self.repo.create_order(
            order_no=self._order_no(),
            user_id=user_id,
            shipping_address=shipping_address,
            coupon_code=coupon.code if coupon else None,
            points_used=pricing.points_used,
            subtotal_amount=pricing.subtotal,
            discount_amount=pricing.discount,
            total_amount=pricing.total,
            items=order_items,
        )

    def update_order(self, order_id: int, payload: dict):
        order = self.repo.get_order(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        if order.payment_status == "paid" and "shipping_address" in payload:
            raise HTTPException(status_code=400, detail="Paid order shipping address cannot be changed")
        if "shipping_address" in payload and payload["shipping_address"]:
            order.shipping_address = payload["shipping_address"]
        if "status" in payload and payload["status"]:
            order.status = payload["status"]
        self.repo.db.add(order)
        self.repo.db.commit()
        self.repo.db.refresh(order)
        return self.repo.get_order(order_id) or order

    def _trigger_low_stock_flow(self, product: Product) -> None:
        threshold = settings.stock_low_threshold
        open_alert = self.repo.get_open_alert(product_id=product.id)
        if product.stock < threshold:
            product.status = "archived"
            self.repo.db.add(product)
            if not open_alert:
                self.repo.create_alert(
                    product_id=product.id,
                    threshold=threshold,
                    stock_snapshot=product.stock,
                    message=f"{product.name} low stock: {product.stock}",
                )
            pending_request = self.repo.get_pending_restock_request(product_id=product.id)
            if not pending_request:
                supplier_resp = self.supplier_service.request_restock(
                    product_id=product.id,
                    quantity=settings.auto_restock_quantity,
                )
                self.repo.create_restock_request(
                    product_id=product.id,
                    requested_quantity=settings.auto_restock_quantity,
                    status="requested" if supplier_resp.get("accepted") else "failed",
                    external_ref=supplier_resp.get("external_ref", ""),
                    provider_response=supplier_resp.get("message", ""),
                )
                try:
                    self.email_service.send_mail(
                        to_email=settings.admin_default_email,
                        subject=f"[Low Stock] {product.name}",
                        body=f"库存低于阈值({threshold})，当前库存={product.stock}，已创建补货请求。",
                    )
                except Exception:  # noqa: BLE001
                    pass
        else:
            if product.status != "active":
                product.status = "active"
                self.repo.db.add(product)
            if open_alert:
                self.repo.resolve_alert(open_alert)

    def pay_order(
        self,
        *,
        order_id: int,
        payment_reference: str | None = None,
        payment_method: str = "mock",
        payer_name: str | None = None,
        coupon_code: str | None = None,
        simulate_failure: bool = False,
    ):
        order = self.repo.get_order(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        if order.payment_status == "paid":
            return order
        if order.status == "cancelled":
            raise HTTPException(status_code=400, detail="Cancelled order cannot be paid")

        coupon: Coupon | None = None
        if coupon_code and coupon_code.strip():
            raw_coupon = self.repo.get_coupon_by_code(coupon_code.strip())
            if not raw_coupon:
                raise HTTPException(status_code=400, detail="Coupon does not exist")
            coupon = self._assert_coupon_valid(raw_coupon)
        elif order.coupon_code:
            coupon = self._assert_coupon_valid(self.repo.get_coupon_by_code(order.coupon_code))

        pricing = calculate_order_pricing(
            subtotal=money(order.subtotal_amount),
            coupon=coupon,
            points_to_use=order.points_used,
            user_points_balance=order.points_used,
        )
        order.points_used = pricing.points_used
        order.discount_amount = pricing.discount
        order.total_amount = pricing.total
        order.coupon_code = coupon.code if coupon else None

        payload_text = (
            f"payer_name={payer_name or ''};"
            f"payment_reference={payment_reference or ''};"
            f"method={payment_method};"
            f"coupon_code={order.coupon_code or ''};"
            f"simulate_failure={simulate_failure}"
        )
        payment_attempt = self.repo.create_payment_attempt(
            payment_no=self._payment_no(),
            order_id=order.id,
            method=payment_method,
            amount=money(order.total_amount),
            payment_reference=payment_reference or "",
            raw_payload=payload_text,
        )

        if simulate_failure:
            self.repo.mark_payment_failed(payment_attempt, reason="Simulated payment failure by request")
            order.payment_status = "failed"
            self.repo.db.add(order)
            self.repo.db.commit()
            return self.repo.get_order(order.id) or order

        product_ids = [item.product_id for item in order.items]
        products = {item.id: item for item in self.repo.lock_products_by_ids(product_ids)}
        for item in order.items:
            product = products[item.product_id]
            if product.stock < item.quantity:
                raise HTTPException(status_code=400, detail=f"Insufficient stock at payment: {product.name}")

        for item in order.items:
            product = products[item.product_id]
            product.stock -= item.quantity
            self.repo.add_behavior_event(user_id=order.user_id, product_id=product.id, event_type="purchase", weight=5)
            self._trigger_low_stock_flow(product)

        user = self.repo.get_user(order.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if order.points_used > 0:
            user.points_balance = max(0, user.points_balance - order.points_used)
        earned_points = int(order.total_amount * Decimal(settings.points_earn_rate))
        user.points_balance += max(earned_points, 0)
        self.repo.db.add(user)

        if order.coupon_code:
            coupon = self.repo.get_coupon_by_code(order.coupon_code)
            if coupon:
                coupon.used_count += 1
                self.repo.db.add(coupon)

        order.payment_status = "paid"
        order.status = "fulfilled"
        order.shipping_status = "requested"
        order.paid_at = datetime.now(timezone.utc)
        self.repo.db.add(order)
        self.repo.mark_payment_succeeded(payment_attempt)

        payload = f"order_no={order.order_no}, payment_ref={payment_reference or ''}"
        self.repo.add_shipment_request(order_id=order.id, payload=payload)
        self.repo.db.commit()
        self._ensure_logistics_trace(order)
        refreshed = self.repo.get_order(order.id) or order
        return refreshed

    def list_user_orders(self, *, user_id: int, page: int, page_size: int):
        if not self.repo.get_user(user_id):
            raise HTTPException(status_code=404, detail="User not found")
        return self.repo.list_orders_by_user(user_id=user_id, page=page, page_size=page_size)

    def list_order_payments(self, *, order_id: int):
        order = self.repo.get_order(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        return self.repo.list_payments_by_order(order_id=order_id)

    def get_order_logistics(self, *, order_id: int) -> dict:
        order = self.repo.get_order(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        if not settings.logistics_service_enabled:
            raise HTTPException(status_code=503, detail="Logistics service is disabled")
        return self._call_logistics(method="GET", path=f"/orders/{order.order_no}")

    def record_view(self, *, user_id: int, product_id: int) -> None:
        if not self.repo.get_user(user_id):
            raise HTTPException(status_code=404, detail="User not found")
        product = self.repo.get_product_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        self.repo.add_behavior_event(user_id=user_id, product_id=product_id, event_type="view", weight=1)
        self.repo.db.commit()

    def get_recommendations(self, *, user_id: int, limit: int = 8):
        if not self.repo.get_user(user_id):
            raise HTTPException(status_code=404, detail="User not found")
        ranked = self.repo.top_behavior_products(user_id=user_id, limit=limit * 3)
        if not ranked:
            products, _ = self.repo.list_products_with_stock(page=1, page_size=limit)
            return [(item.id, 1.0) for item in products if item.status == "active"][:limit]

        product_ids = [pid for pid, _ in ranked]
        products = {item.id: item for item in self.repo.lock_products_by_ids(product_ids)}
        results = []
        for pid, score in ranked:
            product = products.get(pid)
            if not product or product.status != "active":
                continue
            results.append((pid, float(score)))
            if len(results) >= limit:
                break
        return results

    def report_summary(self, *, range_type: str):
        now = datetime.now(timezone.utc)
        if range_type == "daily":
            from_date = now - timedelta(days=1)
        elif range_type == "weekly":
            from_date = now - timedelta(days=7)
        elif range_type == "monthly":
            from_date = now - timedelta(days=30)
        else:
            raise HTTPException(status_code=400, detail="Unsupported range type")

        try:
            paid_count, total_sales = self.repo.paid_orders_between(from_date=from_date, to_date=now)
            low_stock_count = self.repo.low_stock_product_count(settings.stock_low_threshold)
            product_count = self.repo.total_product_count()
        except ProgrammingError as exc:
            # Graceful fallback when mall tables are not migrated yet.
            if "shop_orders" in str(exc):
                paid_count, total_sales, low_stock_count, product_count = 0, Decimal("0"), 0, 0
            else:
                raise
        return {
            "range": range_type,
            "from_date": from_date,
            "to_date": now,
            "total_sales_amount": money(total_sales),
            "paid_order_count": paid_count,
            "low_stock_product_count": low_stock_count,
            "total_product_count": product_count,
        }

    def complete_restock(self, *, request_id: int, quantity: int):
        request = self.repo.get_restock_request(request_id)
        if not request:
            raise HTTPException(status_code=404, detail="Restock request not found")
        product = self.repo.get_product_by_id(request.product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        product.stock += quantity
        request.status = "completed"
        request.completed_at = datetime.now(timezone.utc)
        self.repo.db.add(product)
        self.repo.db.add(request)
        self._trigger_low_stock_flow(product)
        self.repo.db.commit()
        self.repo.db.refresh(request)
        return request
