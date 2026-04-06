export interface ShopProductInventory {
  id: number;
  slug: string;
  name: string;
  price: string;
  status: string;
  stock: number;
  low_stock_threshold: number;
  low_stock: boolean;
}

export interface ShopProductInventoryListResponse {
  page: number;
  page_size: number;
  total: number;
  items: ShopProductInventory[];
}

export interface ShopUser {
  id: number;
  email: string;
  name: string;
  points_balance: number;
  is_active: boolean;
}

export interface ShopOrderItem {
  id: number;
  product_id: number;
  quantity: number;
  unit_price: string;
  line_total: string;
}

export interface ShopOrder {
  id: number;
  order_no: string;
  user_id: number;
  status: "created" | "cancelled" | "fulfilled";
  payment_status: "pending" | "paid" | "failed" | "refunded";
  shipping_status: "pending" | "requested" | "shipped";
  coupon_code?: string | null;
  points_used: number;
  subtotal_amount: string;
  discount_amount: string;
  total_amount: string;
  paid_at?: string | null;
  shipping_address: string;
  created_at: string;
  updated_at: string;
  items: ShopOrderItem[];
}

export interface ShopOrderListResponse {
  page: number;
  page_size: number;
  total: number;
  items: ShopOrder[];
}

export interface ShopRecommendationResponse {
  user_id: number;
  items: Array<{ product_id: number; score: number }>;
}

export interface ShopReportSummary {
  range: "daily" | "weekly" | "monthly";
  from_date: string;
  to_date: string;
  total_sales_amount: string;
  paid_order_count: number;
  low_stock_product_count: number;
  total_product_count: number;
}
