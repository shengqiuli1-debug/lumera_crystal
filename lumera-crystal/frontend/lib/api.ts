import { Category, Post, PostListResponse, Product, ProductListResponse } from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

const emptyProductList: ProductListResponse = { page: 1, page_size: 12, total: 0, items: [] };
const emptyPostList: PostListResponse = { page: 1, page_size: 9, total: 0, items: [] };

async function apiFetch<T>(path: string): Promise<T> {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      next: { revalidate: 60 }
    });
    if (!response.ok) {
      throw new Error(`Request failed: ${response.status}`);
    }
    return response.json() as Promise<T>;
  } catch (error) {
    const message = error instanceof Error ? error.message : "Request failed";
    throw new Error(message);
  }
}

export async function getCategories(): Promise<Category[]> {
  try {
    return await apiFetch<Category[]>("/categories");
  } catch (error) {
    console.error("getCategories failed:", error);
    return [];
  }
}

export async function getCategory(slug: string): Promise<Category> {
  return apiFetch<Category>(`/categories/${slug}`);
}

export async function getProducts(params?: Record<string, string | number | undefined>): Promise<ProductListResponse> {
  const query = new URLSearchParams();
  Object.entries(params ?? {}).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      query.set(key, String(value));
    }
  });
  const suffix = query.toString() ? `?${query.toString()}` : "";
  try {
    return await apiFetch<ProductListResponse>(`/products${suffix}`);
  } catch (error) {
    console.error("getProducts failed:", error);
    return { ...emptyProductList, page: Number(params?.page ?? 1), page_size: Number(params?.page_size ?? 12) };
  }
}

export async function getProduct(slug: string): Promise<Product> {
  return apiFetch<Product>(`/products/${slug}`);
}

export async function getPosts(params?: Record<string, string | number | undefined>): Promise<PostListResponse> {
  const query = new URLSearchParams();
  Object.entries(params ?? {}).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      query.set(key, String(value));
    }
  });
  const suffix = query.toString() ? `?${query.toString()}` : "";
  try {
    return await apiFetch<PostListResponse>(`/posts${suffix}`);
  } catch (error) {
    console.error("getPosts failed:", error);
    return { ...emptyPostList, page: Number(params?.page ?? 1), page_size: Number(params?.page_size ?? 9) };
  }
}

export async function getPost(slug: string): Promise<Post> {
  return apiFetch<Post>(`/posts/${slug}`);
}

export async function submitContact(payload: {
  name: string;
  email: string;
  subject: string;
  message: string;
}): Promise<{ id: number; auto_reply_status?: string | null }> {
  try {
    const response = await fetch(`${API_BASE_URL}/contact`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!response.ok) {
      const raw = await response.text();
      let detail: unknown = raw;
      try {
        const parsed = raw ? JSON.parse(raw) : null;
        detail = parsed && typeof parsed === "object" && "detail" in parsed ? parsed.detail : parsed;
      } catch {
        detail = raw;
      }
      if (Array.isArray(detail) && detail.length > 0 && typeof detail[0] === "object") {
        const first = detail[0] as { msg?: string; loc?: Array<string | number> };
        const loc = first.loc ? ` (${first.loc.join(".")})` : "";
        throw new Error(`表单校验失败${loc}：${first.msg ?? "请检查输入内容"}`);
      }
      throw new Error(typeof detail === "string" ? detail : "提交失败，请稍后再试");
    }
    return response.json() as Promise<{ id: number; auto_reply_status?: string | null }>;
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error(`网络连接失败，无法访问 ${API_BASE_URL}/contact，请确认后端已启动且 CORS 配置正确。`);
    }
    const message = error instanceof Error ? error.message : "提交失败，请稍后再试";
    throw new Error(message);
  }
}

export async function submitNewsletter(payload: { email: string; source?: string }) {
  const response = await fetch(`${API_BASE_URL}/newsletter`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!response.ok) throw new Error("订阅失败");
  return response.json();
}
