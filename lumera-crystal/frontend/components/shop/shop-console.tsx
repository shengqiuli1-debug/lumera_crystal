"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import {
  createShopOrder,
  createShopUser,
  getRecommendations,
  getSalesSummary,
  listShopProducts,
  listUserOrders,
  payShopOrder,
  trackProductView,
} from "@/lib/shop-api";
import type { ShopOrder, ShopProductInventory, ShopReportSummary, ShopUser } from "@/types/shop";

type CartLine = {
  product_id: number;
  quantity: number;
};

const USER_STORAGE_KEY = "lumera_shop_user";

export function ShopConsole() {
  const [products, setProducts] = useState<ShopProductInventory[]>([]);
  const [orders, setOrders] = useState<ShopOrder[]>([]);
  const [recommendations, setRecommendations] = useState<Array<{ product_id: number; score: number }>>([]);
  const [summary, setSummary] = useState<ShopReportSummary | null>(null);
  const [rangeType, setRangeType] = useState<"daily" | "weekly" | "monthly">("daily");

  const [cart, setCart] = useState<CartLine[]>([]);
  const [shippingAddress, setShippingAddress] = useState("上海市浦东新区世纪大道 100 号");
  const [couponCode, setCouponCode] = useState("");
  const [pointsToUse, setPointsToUse] = useState(0);
  const [user, setUser] = useState<ShopUser | null>(null);
  const [name, setName] = useState("体验用户");
  const [email, setEmail] = useState("demo.user@example.com");
  const [toast, setToast] = useState<string>("");
  const [busy, setBusy] = useState(false);

  const productMap = useMemo(() => new Map(products.map((item) => [item.id, item])), [products]);

  const cartTotal = useMemo(() => {
    return cart.reduce((sum, line) => {
      const product = productMap.get(line.product_id);
      if (!product) return sum;
      return sum + Number(product.price) * line.quantity;
    }, 0);
  }, [cart, productMap]);

  const loadBaseData = useCallback(async (currentUser: ShopUser | null) => {
    const [productResult, reportResult] = await Promise.allSettled([
      listShopProducts(1, 50),
      getSalesSummary(rangeType),
    ]);

    if (productResult.status === "fulfilled") {
      setProducts(productResult.value.items);
    } else {
      setToast(
        productResult.reason instanceof Error
          ? `商品数据加载失败：${productResult.reason.message}`
          : "商品数据加载失败，请检查后端服务。"
      );
    }

    if (reportResult.status === "fulfilled") {
      setSummary(reportResult.value);
    } else {
      setSummary(null);
      setToast("报表暂时不可用，已降级为可下单模式。请先完成后端商城迁移。");
    }

    if (!currentUser) return;
    const [orderResult, recResult] = await Promise.allSettled([
      listUserOrders(currentUser.id),
      getRecommendations(currentUser.id, 6),
    ]);
    if (orderResult.status === "fulfilled") {
      setOrders(orderResult.value.items);
    }
    if (recResult.status === "fulfilled") {
      setRecommendations(recResult.value.items);
    }
  }, [rangeType]);

  useEffect(() => {
    const raw = window.localStorage.getItem(USER_STORAGE_KEY);
    if (raw) {
      try {
        const parsed = JSON.parse(raw) as ShopUser;
        setUser(parsed);
      } catch {
        window.localStorage.removeItem(USER_STORAGE_KEY);
      }
    }
  }, []);

  useEffect(() => {
    void loadBaseData(user);
  }, [loadBaseData, user]);

  async function ensureUser() {
    if (user) return user;
    const created = await createShopUser({ name: name.trim(), email: email.trim() });
    setUser(created);
    window.localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(created));
    return created;
  }

  function toggleCart(productId: number) {
    setCart((prev) => {
      const found = prev.find((line) => line.product_id === productId);
      if (found) {
        return prev.filter((line) => line.product_id !== productId);
      }
      return [...prev, { product_id: productId, quantity: 1 }];
    });
  }

  function updateQuantity(productId: number, quantity: number) {
    setCart((prev) => prev.map((line) => (line.product_id === productId ? { ...line, quantity: Math.max(1, quantity) } : line)));
  }

  async function handleView(productId: number) {
    if (!user) return;
    try {
      await trackProductView(user.id, productId);
      const rec = await getRecommendations(user.id, 6);
      setRecommendations(rec.items);
    } catch {
      // ignore analytics errors
    }
  }

  async function handleCreateOrder() {
    if (!cart.length) {
      setToast("请先选择至少一个商品。");
      return;
    }
    setBusy(true);
    try {
      const currentUser = await ensureUser();
      const created = await createShopOrder({
        user_id: currentUser.id,
        shipping_address: shippingAddress,
        coupon_code: couponCode || undefined,
        points_to_use: pointsToUse,
        items: cart,
      });
      setToast(`订单已创建：${created.order_no}`);
      setCart([]);
      const orderRes = await listUserOrders(currentUser.id);
      setOrders(orderRes.items);
    } catch (error) {
      setToast(error instanceof Error ? error.message : "创建订单失败");
    } finally {
      setBusy(false);
    }
  }

  async function handlePayOrder(orderId: number) {
    setBusy(true);
    try {
      const paid = await payShopOrder(orderId, `PAY-${Date.now()}`);
      setToast(`支付成功：${paid.order_no}，已触发库存扣减与发货请求`);
      if (user) {
        const [orderRes, recRes] = await Promise.all([
          listUserOrders(user.id),
          getRecommendations(user.id, 6),
        ]);
        setOrders(orderRes.items);
        setRecommendations(recRes.items);
      }
      const productRes = await listShopProducts(1, 50);
      setProducts(productRes.items);
    } catch (error) {
      setToast(error instanceof Error ? error.message : "支付失败");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-mist/70 bg-white/85 p-5">
        <h3 className="mb-3 text-base font-semibold text-ink">用户与下单设置</h3>
        <div className="grid gap-3 md:grid-cols-2">
          <input className="rounded-lg border border-mist px-3 py-2 text-sm" value={name} onChange={(e) => setName(e.target.value)} placeholder="用户姓名" />
          <input className="rounded-lg border border-mist px-3 py-2 text-sm" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="用户邮箱" />
          <input className="rounded-lg border border-mist px-3 py-2 text-sm md:col-span-2" value={shippingAddress} onChange={(e) => setShippingAddress(e.target.value)} placeholder="收货地址" />
          <input className="rounded-lg border border-mist px-3 py-2 text-sm" value={couponCode} onChange={(e) => setCouponCode(e.target.value)} placeholder="优惠券代码（可选）" />
          <input className="rounded-lg border border-mist px-3 py-2 text-sm" type="number" min={0} value={pointsToUse} onChange={(e) => setPointsToUse(Number(e.target.value || 0))} placeholder="积分抵扣" />
        </div>
        {user ? <p className="mt-2 text-xs text-ink/70">当前用户：{user.name}（ID {user.id}）</p> : null}
      </section>

      <section className="rounded-2xl border border-mist/70 bg-white/85 p-5">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-base font-semibold text-ink">商品库存与下单</h3>
          <span className="text-sm text-ink/70">购物车金额：¥{cartTotal.toFixed(2)}</span>
        </div>
        <div className="grid gap-3 md:grid-cols-2">
          {products.map((product) => {
            const line = cart.find((item) => item.product_id === product.id);
            return (
              <div key={product.id} className="rounded-xl border border-mist p-3">
                <div className="flex items-center justify-between">
                  <p className="font-medium text-ink">{product.name}</p>
                  <p className="text-sm text-ink/70">¥{product.price}</p>
                </div>
                <p className="mt-1 text-xs text-ink/60">库存 {product.stock} · 状态 {product.status}</p>
                {product.low_stock ? <p className="mt-1 text-xs text-amber-700">低库存预警：低于 {product.low_stock_threshold}</p> : null}
                <div className="mt-3 flex items-center gap-2">
                  <button type="button" onClick={() => toggleCart(product.id)} className="rounded-lg border border-stone-300 px-3 py-1.5 text-xs">
                    {line ? "移出购物车" : "加入购物车"}
                  </button>
                  {line ? (
                    <input
                      className="w-20 rounded-lg border border-mist px-2 py-1 text-xs"
                      type="number"
                      min={1}
                      value={line.quantity}
                      onChange={(e) => updateQuantity(product.id, Number(e.target.value || 1))}
                    />
                  ) : null}
                  <button type="button" onClick={() => handleView(product.id)} className="rounded-lg border border-stone-300 px-3 py-1.5 text-xs">
                    模拟浏览
                  </button>
                </div>
              </div>
            );
          })}
        </div>
        <button
          type="button"
          onClick={handleCreateOrder}
          disabled={busy}
          className="mt-4 rounded-lg bg-ink px-4 py-2 text-sm text-ivory disabled:opacity-60"
        >
          {busy ? "处理中..." : "创建订单"}
        </button>
      </section>

      <section className="rounded-2xl border border-mist/70 bg-white/85 p-5">
        <h3 className="mb-3 text-base font-semibold text-ink">订单历史与支付</h3>
        <div className="space-y-2">
          {orders.length === 0 ? <p className="text-sm text-ink/65">暂无订单</p> : null}
          {orders.map((order) => (
            <div key={order.id} className="rounded-xl border border-mist p-3">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-ink">{order.order_no}</p>
                <p className="text-xs text-ink/70">{order.payment_status}</p>
              </div>
              <p className="mt-1 text-xs text-ink/65">
                金额 ¥{order.total_amount} · 商品数 {order.items.length} · 积分抵扣 {order.points_used}
              </p>
              {order.payment_status !== "paid" ? (
                <button type="button" onClick={() => handlePayOrder(order.id)} className="mt-2 rounded-lg border border-stone-300 px-3 py-1.5 text-xs">
                  立即支付（模拟）
                </button>
              ) : (
                <p className="mt-2 text-xs text-emerald-700">已支付并触发发货请求</p>
              )}
            </div>
          ))}
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-mist/70 bg-white/85 p-5">
          <h3 className="mb-3 text-base font-semibold text-ink">个性化推荐</h3>
          {recommendations.length === 0 ? <p className="text-sm text-ink/65">暂无推荐数据（先模拟浏览或下单）</p> : null}
          <div className="space-y-2">
            {recommendations.map((item) => (
              <p key={item.product_id} className="text-sm text-ink/80">
                商品 ID {item.product_id} · 推荐分 {item.score.toFixed(1)}
              </p>
            ))}
          </div>
        </div>

        <div className="rounded-2xl border border-mist/70 bg-white/85 p-5">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-base font-semibold text-ink">销售与库存报表</h3>
            <select
              className="rounded-lg border border-mist px-2 py-1 text-xs"
              value={rangeType}
              onChange={(e) => setRangeType(e.target.value as "daily" | "weekly" | "monthly")}
            >
              <option value="daily">日</option>
              <option value="weekly">周</option>
              <option value="monthly">月</option>
            </select>
          </div>
          {summary ? (
            <div className="space-y-1 text-sm text-ink/80">
              <p>销售额：¥{summary.total_sales_amount}</p>
              <p>已支付订单：{summary.paid_order_count}</p>
              <p>低库存商品：{summary.low_stock_product_count}</p>
              <p>商品总数：{summary.total_product_count}</p>
            </div>
          ) : (
            <p className="text-sm text-ink/65">报表加载中...</p>
          )}
        </div>
      </section>

      {toast ? <p className="rounded-xl border border-mist bg-white px-4 py-3 text-sm text-ink/80">{toast}</p> : null}
    </div>
  );
}
