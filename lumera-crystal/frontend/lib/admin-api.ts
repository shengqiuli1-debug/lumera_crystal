import { clearAdminAuth, getAdminToken } from "@/lib/admin-auth";
import type {
  AdminCategory,
  AdminLoginResponse,
  AdminMediaAsset,
  AdminMessage,
  AdminMessageListResponse,
  AdminNewsletterListResponse,
  AdminPost,
  AdminPostListResponse,
  AdminProduct,
  AdminProductListResponse,
  DashboardOverviewResponse,
} from "@/types/admin";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

type FetchOptions = {
  method?: string;
  body?: unknown;
  skipAuth?: boolean;
};

export class AdminApiError extends Error {
  status: number;
  detail?: unknown;

  constructor(message: string, status: number, detail?: unknown) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

function parseApiErrorMessage(status: number, detail: unknown): string {
  if (typeof detail === "string" && detail.trim()) return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as { msg?: string; loc?: Array<string | number> };
    if (first?.msg) {
      const loc = Array.isArray(first.loc) ? `(${first.loc.join(".")}) ` : "";
      return `参数校验失败 ${loc}${first.msg}`;
    }
  }
  if (detail && typeof detail === "object" && "message" in detail) {
    const msg = (detail as { message?: string }).message;
    if (msg) return msg;
  }
  if (status === 401) return "登录已过期，请重新登录";
  if (status === 403) return "没有权限执行该操作";
  if (status === 404) return "资源不存在或已被删除";
  if (status === 422) return "提交数据校验失败，请检查字段格式";
  if (status >= 500) return "服务器内部错误，请稍后重试";
  return `请求失败 (${status})`;
}

async function adminFetch<T>(path: string, options: FetchOptions = {}): Promise<T> {
  const headers: HeadersInit = {};
  if (!options.skipAuth) {
    const token = getAdminToken();
    if (!token) {
      throw new AdminApiError("未登录", 401);
    }
    headers.Authorization = `Bearer ${token}`;
  }
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: options.method ?? "GET",
      headers,
      body: options.body instanceof FormData ? options.body : options.body ? JSON.stringify(options.body) : undefined,
      cache: "no-store",
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Load failed";
    throw new AdminApiError(`网络请求失败：${message}。请检查后端服务和 API 地址。`, 0, error);
  }

  if (!response.ok) {
    const raw = await response.text().catch(() => "");
    let detail: unknown = raw;
    try {
      const parsed = raw ? JSON.parse(raw) : null;
      detail = parsed && typeof parsed === "object" && "detail" in parsed ? parsed.detail : parsed;
    } catch {
      detail = raw;
    }
    if (response.status === 401) {
      clearAdminAuth();
    }
    throw new AdminApiError(parseApiErrorMessage(response.status, detail), response.status, detail);
  }
  return response.json() as Promise<T>;
}

export async function adminLogin(payload: { email: string; password: string }): Promise<AdminLoginResponse> {
  return adminFetch<AdminLoginResponse>("/admin/auth/login", { method: "POST", body: payload, skipAuth: true });
}

export async function adminGetMe() {
  return adminFetch("/admin/auth/me");
}

export async function adminLogout() {
  return adminFetch("/admin/auth/logout", { method: "POST" });
}

export async function getDashboardOverview(): Promise<DashboardOverviewResponse> {
  return adminFetch<DashboardOverviewResponse>("/admin/dashboard/overview");
}

export async function getAdminProducts(params?: Record<string, string | number | boolean | undefined>) {
  const query = new URLSearchParams();
  Object.entries(params ?? {}).forEach(([key, value]) => {
    if (value !== undefined && value !== "") query.set(key, String(value));
  });
  return adminFetch<AdminProductListResponse>(`/admin/products?${query.toString()}`);
}

export async function getAdminProduct(id: number): Promise<AdminProduct> {
  return adminFetch<AdminProduct>(`/admin/products/${id}`);
}

export async function createAdminProduct(payload: Partial<AdminProduct>): Promise<AdminProduct> {
  return adminFetch<AdminProduct>("/admin/products", { method: "POST", body: payload });
}

export async function updateAdminProduct(id: number, payload: Partial<AdminProduct>): Promise<AdminProduct> {
  return adminFetch<AdminProduct>(`/admin/products/${id}`, { method: "PATCH", body: payload });
}

export async function deleteAdminProduct(id: number) {
  return adminFetch(`/admin/products/${id}`, { method: "DELETE" });
}

export async function bulkStatusAdminProduct(ids: number[], status: string) {
  return adminFetch<{ updated_count: number }>("/admin/products/bulk-status", {
    method: "POST",
    body: { ids, status },
  });
}

export async function getAdminCategories(search?: string): Promise<AdminCategory[]> {
  const suffix = search ? `?search=${encodeURIComponent(search)}` : "";
  return adminFetch<AdminCategory[]>(`/admin/categories${suffix}`);
}

export async function getAdminCategory(id: number): Promise<AdminCategory> {
  return adminFetch<AdminCategory>(`/admin/categories/${id}`);
}

export async function createAdminCategory(payload: Partial<AdminCategory>) {
  return adminFetch<AdminCategory>("/admin/categories", { method: "POST", body: payload });
}

export async function updateAdminCategory(id: number, payload: Partial<AdminCategory>) {
  return adminFetch<AdminCategory>(`/admin/categories/${id}`, { method: "PATCH", body: payload });
}

export async function deleteAdminCategory(id: number) {
  return adminFetch(`/admin/categories/${id}`, { method: "DELETE" });
}

export async function getAdminPosts(params?: Record<string, string | number | undefined>) {
  const query = new URLSearchParams();
  Object.entries(params ?? {}).forEach(([key, value]) => {
    if (value !== undefined && value !== "") query.set(key, String(value));
  });
  return adminFetch<AdminPostListResponse>(`/admin/posts?${query.toString()}`);
}

export async function getAdminPost(id: number): Promise<AdminPost> {
  return adminFetch<AdminPost>(`/admin/posts/${id}`);
}

export async function createAdminPost(payload: Partial<AdminPost>) {
  return adminFetch<AdminPost>("/admin/posts", { method: "POST", body: payload });
}

export async function updateAdminPost(id: number, payload: Partial<AdminPost>) {
  return adminFetch<AdminPost>(`/admin/posts/${id}`, { method: "PATCH", body: payload });
}

export async function deleteAdminPost(id: number) {
  return adminFetch(`/admin/posts/${id}`, { method: "DELETE" });
}

export async function getAdminMessages(params?: Record<string, string | number | boolean | undefined>) {
  const query = new URLSearchParams();
  Object.entries(params ?? {}).forEach(([key, value]) => {
    if (value !== undefined && value !== "") query.set(key, String(value));
  });
  return adminFetch<AdminMessageListResponse>(`/admin/messages?${query.toString()}`);
}

export async function getAdminMessage(id: number): Promise<AdminMessage> {
  return adminFetch<AdminMessage>(`/admin/messages/${id}`);
}

export async function markAdminMessageRead(id: number, isRead: boolean) {
  return adminFetch<AdminMessage>(`/admin/messages/${id}/read`, {
    method: "PATCH",
    body: { is_read: isRead },
  });
}

export async function replyAdminMessage(id: number, replyContent: string) {
  return adminFetch<AdminMessage>(`/admin/messages/${id}/reply`, {
    method: "POST",
    body: { reply_content: replyContent },
  });
}

export async function getAdminNewsletter(params?: Record<string, string | number | undefined>) {
  const query = new URLSearchParams();
  Object.entries(params ?? {}).forEach(([key, value]) => {
    if (value !== undefined && value !== "") query.set(key, String(value));
  });
  return adminFetch<AdminNewsletterListResponse>(`/admin/newsletter?${query.toString()}`);
}

export async function uploadAdminImage(file: File): Promise<{
  id: number;
  url: string;
  file_name: string;
  mime_type: string;
  media_kind: string;
  file_size: number;
  duration_seconds?: number | null;
}> {
  const formData = new FormData();
  formData.append("file", file);
  return adminFetch<AdminMediaAsset>(
    "/admin/uploads/image",
    {
      method: "POST",
      body: formData,
    }
  );
}
