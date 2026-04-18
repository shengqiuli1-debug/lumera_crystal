"use client";

import { useEffect, useMemo, useState } from "react";

import { clearCart, getCart, removeFromCart, type CartItem, updateCartQuantity } from "@/lib/cart";
import { createShopOrder, createShopUser, listUserOrders, payShopOrder } from "@/lib/shop-api";
import type { ShopOrder, ShopPaymentMethod, ShopUser } from "@/types/shop";

const USER_STORAGE_KEY = "lumera_shop_user";

function formatMoney(value: number | string) {
  return Number(value).toFixed(2);
}

export function CartCheckout() {
  const [cart, setCart] = useState<CartItem[]>([]);
  const [user, setUser] = useState<ShopUser | null>(null);
  const [name, setName] = useState("体验用户");
  const [email, setEmail] = useState("demo.user@example.com");
  const shippingAddress = "上海市浦东新区世纪大道 100 号";
  const [paymentMethod, setPaymentMethod] = useState<ShopPaymentMethod>("wechat_pay");
  const [payerName, setPayerName] = useState("体验用户");
  const [payCouponCode, setPayCouponCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [pendingOrders, setPendingOrders] = useState<ShopOrder[]>([]);
  const [payNowOrder, setPayNowOrder] = useState<ShopOrder | null>(null);
  const [toast, setToast] = useState("");

  const subtotal = useMemo(() => {
    return cart.reduce((sum, line) => sum + Number(line.price) * line.quantity, 0);
  }, [cart]);

  const cartCount = useMemo(() => cart.reduce((sum, line) => sum + line.quantity, 0), [cart]);

  useEffect(() => {
    setCart(getCart());
    const raw = window.localStorage.getItem(USER_STORAGE_KEY);
    if (!raw) return;
    try {
      const parsed = JSON.parse(raw) as ShopUser;
      setUser(parsed);
      setName(parsed.name);
      setEmail(parsed.email);
      setPayerName(parsed.name);
    } catch {
      window.localStorage.removeItem(USER_STORAGE_KEY);
    }
  }, []);

  useEffect(() => {
    if (!user) return;
    void refreshPendingOrders(user.id);
  }, [user]);

  async function ensureUser() {
    if (user) return user;
    const created = await createShopUser({ name: name.trim(), email: email.trim() });
    setUser(created);
    window.localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(created));
    return created;
  }

  async function refreshPendingOrders(currentUserId: number) {
    const resp = await listUserOrders(currentUserId);
    setPendingOrders(resp.items.filter((item) => item.payment_status !== "paid"));
  }

  async function handleSubmitOrder() {
    if (!cart.length) {
      setToast("购物车为空，请先添加商品。");
      return;
    }

    setBusy(true);
    try {
      const currentUser = await ensureUser();
      const created = await createShopOrder({
        user_id: currentUser.id,
        shipping_address: shippingAddress,
        points_to_use: 0,
        items: cart.map((line) => ({ product_id: line.product_id, quantity: line.quantity }))
      });
      clearCart();
      setCart([]);
      await refreshPendingOrders(currentUser.id);
      setPayNowOrder(created);
      setToast("订单已创建，已弹出支付窗口。");
    } catch (error) {
      setToast(error instanceof Error ? error.message : "下单失败");
    } finally {
      setBusy(false);
    }
  }

  async function handlePay(orderId: number) {
    setBusy(true);
    try {
      const paid = await payShopOrder({
        orderId,
        paymentMethod,
        paymentReference: `PAY-${Date.now()}`,
        payerName: payerName.trim() || undefined,
        couponCode: payCouponCode.trim() || undefined,
        simulateFailure: false
      });
      if (paid.payment_status === "paid") {
        setToast(`支付成功：${paid.order_no}`);
        setPayNowOrder((current) => (current?.id === orderId ? null : current));
        setPayCouponCode("");
      } else {
        setToast(`支付未成功：${paid.order_no}`);
      }
      if (user) {
        await refreshPendingOrders(user.id);
      }
    } catch (error) {
      setToast(error instanceof Error ? error.message : "支付失败");
    } finally {
      setBusy(false);
    }
  }

  function onRemoveItem(productId: number) {
    setCart(removeFromCart(productId));
  }

  function onChangeQty(productId: number, quantity: number) {
    setCart(updateCartQuantity(productId, quantity));
  }

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-mist/70 bg-gradient-to-br from-white to-ivory p-5 shadow-[0_10px_35px_-24px_rgba(39,37,34,0.65)]">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-base font-semibold text-ink">购物流程</h2>
          <p className="text-xs text-ink/65">详情页加入商品 → 购物车下单 → 支付完成</p>
        </div>
        <div className="mt-3 grid gap-2 text-xs md:grid-cols-3">
          <div className="rounded-xl border border-amber-200 bg-amber-50/70 px-3 py-2 text-amber-900">1. 确认商品</div>
          <div className="rounded-xl border border-sky-200 bg-sky-50/70 px-3 py-2 text-sky-900">2. 提交订单</div>
          <div className="rounded-xl border border-emerald-200 bg-emerald-50/70 px-3 py-2 text-emerald-900">3. 完成支付</div>
        </div>
      </section>

      <div className="space-y-6">
        <section className="rounded-3xl border border-mist/70 bg-white/90 p-5 shadow-[0_12px_30px_-24px_rgba(32,30,27,0.7)]">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-semibold text-ink">购物车</h2>
              <p className="text-xs text-ink/65">当前使用默认收货信息快速下单</p>
            </div>
            <span className="rounded-full border border-mist px-2.5 py-1 text-xs text-ink/70">{cartCount} 件商品</span>
          </div>
          {cart.length === 0 ? <p className="text-sm text-ink/65">购物车为空，去商品详情页添加商品吧。</p> : null}
          <div className="space-y-3">
            {cart.map((line) => (
              <div
                key={line.product_id}
                className="flex flex-wrap items-center gap-3 rounded-2xl border border-mist/80 bg-ivory/40 p-3"
              >
                <img src={line.cover_image} alt={line.name} className="h-16 w-16 rounded-lg object-cover" />
                <div className="min-w-[180px] flex-1">
                  <p className="text-sm font-medium text-ink">{line.name}</p>
                  <p className="text-xs text-ink/70">单价 ¥{line.price}</p>
                </div>
                <input
                  className="w-20 rounded-lg border border-mist bg-white px-2 py-1 text-sm"
                  type="number"
                  min={1}
                  value={line.quantity}
                  onChange={(e) => onChangeQty(line.product_id, Number(e.target.value || 1))}
                />
                <button
                  type="button"
                  onClick={() => onRemoveItem(line.product_id)}
                  className="rounded-lg border border-stone-300 px-3 py-1.5 text-xs"
                >
                  移除
                </button>
              </div>
            ))}
          </div>
          <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-mist/70 bg-ivory/50 p-3">
            <div className="text-sm text-ink/70">
              商品件数 <span className="font-medium text-ink">{cartCount}</span> · 小计{" "}
              <span className="font-medium text-ink">¥{formatMoney(subtotal)}</span>
            </div>
            <button
              type="button"
              onClick={handleSubmitOrder}
              disabled={busy || cart.length === 0}
              className="rounded-xl bg-ink px-4 py-2.5 text-sm font-medium text-ivory disabled:cursor-not-allowed disabled:opacity-50"
            >
              {busy ? "处理中..." : "提交订单"}
            </button>
          </div>
        </section>

        <section className="rounded-3xl border border-mist/70 bg-white/90 p-5 shadow-[0_12px_30px_-24px_rgba(32,30,27,0.7)]">
          <h2 className="mb-3 text-base font-semibold text-ink">待支付订单</h2>
            <div className="mb-3 grid gap-3 md:grid-cols-3">
              <select className="rounded-lg border border-mist px-3 py-2 text-sm" value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value as ShopPaymentMethod)}>
                <option value="wechat_pay">微信支付</option>
                <option value="alipay">支付宝</option>
                <option value="bank_card">银行卡</option>
                <option value="mock">测试通道</option>
              </select>
              <input className="rounded-lg border border-mist px-3 py-2 text-sm md:col-span-2" value={payerName} onChange={(e) => setPayerName(e.target.value)} placeholder="付款人（可选）" />
              <input className="rounded-lg border border-mist px-3 py-2 text-sm md:col-span-3" value={payCouponCode} onChange={(e) => setPayCouponCode(e.target.value)} placeholder="优惠券代码（支付时使用）" />
            </div>
            {pendingOrders.length === 0 ? <p className="text-sm text-ink/65">暂无待支付订单（提交订单后会显示在这里）。</p> : null}
            <div className="space-y-2">
              {pendingOrders.map((order) => (
                <div key={order.id} className="rounded-2xl border border-mist/80 bg-ivory/40 p-3">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-ink">{order.order_no}</p>
                    <p className="text-xs text-ink/70">应付 ¥{order.total_amount}</p>
                  </div>
                  <p className="mt-1 text-xs text-ink/65">状态：{order.payment_status} · 商品数 {order.items.length}</p>
                  <button
                    type="button"
                    onClick={() => handlePay(order.id)}
                    disabled={busy}
                    className="mt-2 rounded-lg border border-stone-300 px-3 py-1.5 text-xs disabled:opacity-50"
                  >
                    立即支付
                  </button>
                </div>
              ))}
            </div>
        </section>
      </div>

      {toast ? <p className="rounded-xl border border-mist bg-white px-4 py-3 text-sm text-ink/80">{toast}</p> : null}

      {payNowOrder ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/45 p-4">
          <div className="w-full max-w-lg rounded-3xl border border-mist/70 bg-white p-5 shadow-[0_20px_50px_-30px_rgba(20,20,20,0.95)]">
            <div className="mb-3 flex items-start justify-between gap-3">
              <div>
                <h3 className="text-lg font-semibold text-ink">订单已创建，立即支付</h3>
                <p className="mt-1 text-xs text-ink/65">{payNowOrder.order_no}</p>
              </div>
              <button
                type="button"
                onClick={() => setPayNowOrder(null)}
                className="rounded-lg border border-stone-300 px-2.5 py-1 text-xs text-ink/70"
              >
                关闭
              </button>
            </div>

            <div className="rounded-2xl border border-mist/70 bg-ivory/50 p-3 text-sm text-ink/80">
              <div className="flex items-center justify-between">
                <span>应付金额</span>
                <span className="font-medium text-ink">¥{payNowOrder.total_amount}</span>
              </div>
              <div className="mt-1 flex items-center justify-between">
                <span>商品数量</span>
                <span className="text-ink">{payNowOrder.items.length}</span>
              </div>
            </div>

            <div className="mt-3 grid gap-3 md:grid-cols-3">
              <select className="rounded-lg border border-mist px-3 py-2 text-sm" value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value as ShopPaymentMethod)}>
                <option value="wechat_pay">微信支付</option>
                <option value="alipay">支付宝</option>
                <option value="bank_card">银行卡</option>
                <option value="mock">测试通道</option>
              </select>
              <input className="rounded-lg border border-mist px-3 py-2 text-sm md:col-span-2" value={payerName} onChange={(e) => setPayerName(e.target.value)} placeholder="付款人（可选）" />
              <input className="rounded-lg border border-mist px-3 py-2 text-sm md:col-span-3" value={payCouponCode} onChange={(e) => setPayCouponCode(e.target.value)} placeholder="优惠券代码（支付时使用）" />
            </div>

            <div className="mt-4 flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={() => setPayNowOrder(null)}
                className="rounded-xl border border-stone-300 px-4 py-2 text-sm text-ink"
              >
                稍后支付
              </button>
              <button
                type="button"
                onClick={() => handlePay(payNowOrder.id)}
                disabled={busy}
                className="rounded-xl bg-ink px-4 py-2 text-sm font-medium text-ivory disabled:opacity-50"
              >
                {busy ? "支付处理中..." : "立即支付"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
