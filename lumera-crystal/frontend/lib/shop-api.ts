import type {
  ShopOrder,
  ShopOrderListResponse,
  ShopLogisticsTrace,
  ShopPayment,
  ShopPaymentMethod,
  ShopProductInventoryListResponse,
  ShopRecommendationResponse,
  ShopReportSummary,
  ShopUser,
} from "@/types/shop";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

async function shopFetch<T>(path: string, options?: { method?: string; body?: unknown }): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options?.method ?? "GET",
    headers: options?.body ? { "Content-Type": "application/json" } : undefined,
    body: options?.body ? JSON.stringify(options.body) : undefined,
    cache: "no-store",
  });
  if (!response.ok) {
    const raw = await response.text();
    let detail = raw;
    try {
      const parsed = raw ? JSON.parse(raw) : null;
      detail = parsed && typeof parsed === "object" && "detail" in parsed ? String(parsed.detail) : raw;
    } catch {
      detail = raw;
    }
    throw new Error(detail || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function listShopProducts(page = 1, pageSize = 20) {
  return shopFetch<ShopProductInventoryListResponse>(`/shop/products?page=${page}&page_size=${pageSize}`);
}

export function createShopUser(payload: { email: string; name: string }) {
  return shopFetch<ShopUser>("/shop/users", { method: "POST", body: payload });
}

export function createShopOrder(payload: {
  user_id: number;
  shipping_address: string;
  coupon_code?: string;
  points_to_use?: number;
  items: Array<{ product_id: number; quantity: number }>;
}) {
  return shopFetch<ShopOrder>("/shop/orders", { method: "POST", body: payload });
}

export function payShopOrder(payload: {
  orderId: number;
  paymentReference?: string;
  paymentMethod: ShopPaymentMethod;
  payerName?: string;
  couponCode?: string;
  simulateFailure?: boolean;
}) {
  return shopFetch<ShopOrder>(`/shop/orders/${payload.orderId}/pay`, {
    method: "POST",
    body: {
      payment_reference: payload.paymentReference ?? null,
      payment_method: payload.paymentMethod,
      payer_name: payload.payerName ?? null,
      coupon_code: payload.couponCode ?? null,
      simulate_failure: Boolean(payload.simulateFailure),
    },
  });
}

export function listOrderPayments(orderId: number) {
  return shopFetch<ShopPayment[]>(`/shop/orders/${orderId}/payments`);
}

export function getOrderLogistics(orderId: number) {
  return shopFetch<ShopLogisticsTrace>(`/shop/orders/${orderId}/logistics`);
}

export function listUserOrders(userId: number, page = 1, pageSize = 20) {
  return shopFetch<ShopOrderListResponse>(`/shop/users/${userId}/orders?page=${page}&page_size=${pageSize}`);
}

export function trackProductView(userId: number, productId: number) {
  return shopFetch<{ success: boolean }>(`/shop/users/${userId}/events/view/${productId}`, { method: "POST" });
}

export function getRecommendations(userId: number, limit = 8) {
  return shopFetch<ShopRecommendationResponse>(`/shop/users/${userId}/recommendations?limit=${limit}`);
}

export function getSalesSummary(range: "daily" | "weekly" | "monthly") {
  return shopFetch<ShopReportSummary>(`/shop/reports/summary?range=${range}`);
}
