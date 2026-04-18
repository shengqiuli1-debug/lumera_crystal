"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { createShopUser, getOrderLogistics, listUserOrders, payShopOrder } from "@/lib/shop-api";
import type { ShopLogisticsTrace, ShopOrder, ShopPaymentMethod, ShopUser } from "@/types/shop";

const USER_STORAGE_KEY = "lumera_shop_user";

type OrderFilter = "all" | "pending" | "paid";

export function ShopConsole() {
  const [orders, setOrders] = useState<ShopOrder[]>([]);
  const [user, setUser] = useState<ShopUser | null>(null);
  const [name, setName] = useState("体验用户");
  const [email, setEmail] = useState("demo.user@example.com");
  const [toast, setToast] = useState<string>("");
  const [busy, setBusy] = useState(false);

  const [orderFilter, setOrderFilter] = useState<OrderFilter>("all");
  const [payingOrderId, setPayingOrderId] = useState<number | null>(null);
  const [paymentMethod, setPaymentMethod] = useState<ShopPaymentMethod>("wechat_pay");
  const [payerName, setPayerName] = useState("体验用户");
  const [payCouponCode, setPayCouponCode] = useState("");
  const [logisticsMap, setLogisticsMap] = useState<Record<number, ShopLogisticsTrace>>({});
  const [loadingLogisticsOrderId, setLoadingLogisticsOrderId] = useState<number | null>(null);

  const filteredOrders = useMemo(() => {
    if (orderFilter === "pending") return orders.filter((item) => item.payment_status !== "paid");
    if (orderFilter === "paid") return orders.filter((item) => item.payment_status === "paid");
    return orders;
  }, [orders, orderFilter]);

  const pendingCount = useMemo(() => orders.filter((item) => item.payment_status !== "paid").length, [orders]);
  const paidCount = useMemo(() => orders.filter((item) => item.payment_status === "paid").length, [orders]);

  const refreshOrders = useCallback(async (userId: number) => {
    const orderResult = await listUserOrders(userId, 1, 50);
    setOrders(orderResult.items);
  }, []);

  useEffect(() => {
    const raw = window.localStorage.getItem(USER_STORAGE_KEY);
    if (raw) {
      try {
        const parsed = JSON.parse(raw) as ShopUser;
        setUser(parsed);
        setName(parsed.name);
        setEmail(parsed.email);
        setPayerName(parsed.name);
        void refreshOrders(parsed.id);
      } catch {
        window.localStorage.removeItem(USER_STORAGE_KEY);
      }
    }
  }, [refreshOrders]);

  async function ensureUser() {
    if (user) return user;
    const created = await createShopUser({ name: name.trim(), email: email.trim() });
    setUser(created);
    setPayerName(created.name);
    window.localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(created));
    return created;
  }

  async function handleActivateMyOrders() {
    setBusy(true);
    try {
      const currentUser = await ensureUser();
      await refreshOrders(currentUser.id);
      setToast("已进入订单中心。");
    } catch (error) {
      setToast(error instanceof Error ? error.message : "加载订单失败");
    } finally {
      setBusy(false);
    }
  }

  async function handlePayOrder(orderId: number) {
    setBusy(true);
    try {
      const paid = await payShopOrder({
        orderId,
        paymentReference: `PAY-${Date.now()}`,
        paymentMethod,
        payerName: payerName.trim() || undefined,
        couponCode: payCouponCode.trim() || undefined,
        simulateFailure: false,
      });
      if (paid.payment_status === "paid") {
        setToast(`支付成功：${paid.order_no}`);
      } else {
        setToast(`支付失败：${paid.order_no}，可调整后重试`);
      }
      const currentUser = await ensureUser();
      await refreshOrders(currentUser.id);
      setPayingOrderId(null);
      setPayCouponCode("");
    } catch (error) {
      setToast(error instanceof Error ? error.message : "支付失败");
    } finally {
      setBusy(false);
    }
  }

  async function handleLoadLogistics(orderId: number) {
    setLoadingLogisticsOrderId(orderId);
    try {
      const trace = await getOrderLogistics(orderId);
      setLogisticsMap((prev) => ({ ...prev, [orderId]: trace }));
      setToast(`已加载物流信息：${trace.current_label}`);
    } catch (error) {
      setToast(error instanceof Error ? error.message : "物流信息加载失败");
    } finally {
      setLoadingLogisticsOrderId(null);
    }
  }

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-mist/70 bg-gradient-to-br from-white to-ivory p-5 shadow-[0_14px_34px_-26px_rgba(28,28,28,0.9)]">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="text-base font-semibold text-ink">订单中心</h3>
            <p className="mt-1 text-sm text-ink/70">查看已生成订单、待支付订单、已支付订单，并在这里完成支付。</p>
          </div>
          <div className="flex items-center gap-2">
            <input
              className="rounded-lg border border-mist px-3 py-2 text-sm"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="用户名"
            />
            <input
              className="rounded-lg border border-mist px-3 py-2 text-sm"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="邮箱"
            />
            <button
              type="button"
              onClick={handleActivateMyOrders}
              disabled={busy}
              className="rounded-lg bg-ink px-4 py-2 text-sm text-ivory disabled:opacity-60"
            >
              {busy ? "处理中..." : "刷新订单"}
            </button>
          </div>
        </div>
      </section>

      <section className="grid gap-3 sm:grid-cols-3">
        <div className="rounded-2xl border border-mist/70 bg-white/90 p-4 shadow-[0_10px_28px_-24px_rgba(30,30,30,0.85)]">
          <p className="text-xs text-ink/60">全部订单</p>
          <p className="mt-1 text-xl font-semibold text-ink">{orders.length}</p>
        </div>
        <div className="rounded-2xl border border-mist/70 bg-white/90 p-4 shadow-[0_10px_28px_-24px_rgba(30,30,30,0.85)]">
          <p className="text-xs text-ink/60">待支付</p>
          <p className="mt-1 text-xl font-semibold text-ink">{pendingCount}</p>
        </div>
        <div className="rounded-2xl border border-mist/70 bg-white/90 p-4 shadow-[0_10px_28px_-24px_rgba(30,30,30,0.85)]">
          <p className="text-xs text-ink/60">已支付</p>
          <p className="mt-1 text-xl font-semibold text-ink">{paidCount}</p>
        </div>
      </section>

      <section className="rounded-3xl border border-mist/70 bg-gradient-to-br from-white to-ivory p-5 shadow-[0_14px_34px_-26px_rgba(28,28,28,0.9)]">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-base font-semibold text-ink">订单列表</h3>
          <div className="flex items-center gap-2 text-xs">
            <button
              type="button"
              onClick={() => setOrderFilter("all")}
              className={`rounded-full px-2.5 py-1 ${orderFilter === "all" ? "bg-ink text-ivory" : "border border-mist text-ink/70"}`}
            >
              全部
            </button>
            <button
              type="button"
              onClick={() => setOrderFilter("pending")}
              className={`rounded-full px-2.5 py-1 ${orderFilter === "pending" ? "bg-ink text-ivory" : "border border-mist text-ink/70"}`}
            >
              待支付
            </button>
            <button
              type="button"
              onClick={() => setOrderFilter("paid")}
              className={`rounded-full px-2.5 py-1 ${orderFilter === "paid" ? "bg-ink text-ivory" : "border border-mist text-ink/70"}`}
            >
              已支付
            </button>
          </div>
        </div>

        {filteredOrders.length === 0 ? <p className="text-sm text-ink/65">暂无订单记录，请先去晶石商店下单。</p> : null}

        <div className="space-y-2">
          {filteredOrders.map((order) => (
            <div key={order.id} className="rounded-2xl border border-mist bg-white/85 p-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <p className="text-sm font-medium text-ink">{order.order_no}</p>
                  <p className="text-xs text-ink/65">{new Date(order.created_at).toLocaleString()}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-ink">¥{order.total_amount}</p>
                  <p className="text-xs text-ink/65">{order.payment_status === "paid" ? "已支付" : "待支付"}</p>
                </div>
              </div>

              <p className="mt-1 text-xs text-ink/65">商品数 {order.items.length} · 支付状态 {order.payment_status}</p>

              {order.payment_status !== "paid" ? (
                <div className="mt-2 space-y-2">
                  {payingOrderId === order.id ? (
                    <div className="grid gap-2 rounded-lg border border-mist p-2 md:grid-cols-2">
                      <select
                        className="rounded-lg border border-mist px-2 py-1 text-xs"
                        value={paymentMethod}
                        onChange={(e) => setPaymentMethod(e.target.value as ShopPaymentMethod)}
                      >
                        <option value="wechat_pay">微信支付</option>
                        <option value="alipay">支付宝</option>
                        <option value="bank_card">银行卡</option>
                        <option value="mock">测试通道</option>
                      </select>
                      <input
                        className="rounded-lg border border-mist px-2 py-1 text-xs"
                        value={payerName}
                        onChange={(e) => setPayerName(e.target.value)}
                        placeholder="付款人（可选）"
                      />
                      <input
                        className="rounded-lg border border-mist px-2 py-1 text-xs md:col-span-2"
                        value={payCouponCode}
                        onChange={(e) => setPayCouponCode(e.target.value)}
                        placeholder="优惠券代码（支付时使用）"
                      />
                      <div className="flex items-center gap-2 md:col-span-2">
                        <button
                          type="button"
                          onClick={() => handlePayOrder(order.id)}
                          className="rounded-lg border border-stone-300 px-3 py-1.5 text-xs"
                        >
                          确认支付
                        </button>
                        <button
                          type="button"
                          onClick={() => setPayingOrderId(null)}
                          className="rounded-lg border border-stone-300 px-3 py-1.5 text-xs"
                        >
                          取消
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button
                      type="button"
                      onClick={() => setPayingOrderId(order.id)}
                      className="rounded-lg border border-stone-300 px-3 py-1.5 text-xs"
                    >
                      去支付
                    </button>
                  )}
                </div>
              ) : (
                <div className="mt-2 space-y-2">
                  <p className="text-xs text-emerald-700">已支付完成</p>
                  <button
                    type="button"
                    onClick={() => handleLoadLogistics(order.id)}
                    disabled={loadingLogisticsOrderId === order.id}
                    className="rounded-lg border border-stone-300 px-3 py-1.5 text-xs disabled:opacity-50"
                  >
                    {loadingLogisticsOrderId === order.id ? "物流加载中..." : "查看物流"}
                  </button>
                  {logisticsMap[order.id] ? (
                    <div className="rounded-xl border border-mist/70 bg-ivory/45 p-2">
                      <p className="text-xs font-medium text-ink">
                        当前进度：{logisticsMap[order.id].current_label}（{logisticsMap[order.id].tracking_no}）
                      </p>
                      <div className="mt-1 space-y-1">
                        {logisticsMap[order.id].events.map((event) => (
                          <div key={`${order.id}-${event.step_code}-${event.occurred_at}`} className="text-xs text-ink/70">
                            {new Date(event.occurred_at).toLocaleString()} · {event.step_label}
                            {event.detail ? ` · ${event.detail}` : ""}
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : null}
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {toast ? <p className="rounded-2xl border border-mist bg-white px-4 py-3 text-sm text-ink/80 shadow-[0_10px_28px_-24px_rgba(30,30,30,0.85)]">{toast}</p> : null}
    </div>
  );
}
