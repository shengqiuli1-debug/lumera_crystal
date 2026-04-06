"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { AdminPageShell } from "@/components/admin/page-shell";
import { StatusPill } from "@/components/admin/status-pill";
import { bulkStatusAdminProduct, deleteAdminProduct, getAdminCategories, getAdminProducts } from "@/lib/admin-api";
import type { AdminCategory, AdminProduct, AdminProductListResponse } from "@/types/admin";

export default function AdminProductsPage() {
  const [data, setData] = useState<AdminProductListResponse | null>(null);
  const [categories, setCategories] = useState<AdminCategory[]>([]);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [page, setPage] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const pageSize = 12;

  const load = useCallback(async () => {
    setError(null);
    try {
      const result = await getAdminProducts({
        page,
        page_size: pageSize,
        search: search || undefined,
        status: status || undefined,
        category_id: categoryId || undefined,
      });
      setData(result);
      setSelectedIds([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载失败");
    }
  }, [categoryId, page, search, status]);

  useEffect(() => {
    getAdminCategories().then(setCategories);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function handleDelete(id: number) {
    if (!confirm("确认删除该商品？")) return;
    await deleteAdminProduct(id);
    await load();
  }

  async function handleBulkActive() {
    if (!selectedIds.length) return;
    await bulkStatusAdminProduct(selectedIds, "active");
    await load();
  }

  async function handleBulkArchive() {
    if (!selectedIds.length) return;
    await bulkStatusAdminProduct(selectedIds, "archived");
    await load();
  }

  function toggleItem(item: AdminProduct) {
    setSelectedIds((prev) => (prev.includes(item.id) ? prev.filter((id) => id !== item.id) : [...prev, item.id]));
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;

  return (
    <AdminPageShell
      title="商品管理"
      description="快速搜索、批量上下架、直接进入编辑。"
      actions={
        <Link href="/admin/products/new" className="rounded-lg bg-stone-900 px-3 py-2 text-sm text-white">
          新增商品
        </Link>
      }
    >
      <div className="rounded-2xl border border-stone-200 bg-white p-4">
        <div className="grid gap-3 lg:grid-cols-4">
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="搜索名称/slug" className="rounded-lg border border-stone-300 px-3 py-2 text-sm" />
          <select value={status} onChange={(e) => setStatus(e.target.value)} className="rounded-lg border border-stone-300 px-3 py-2 text-sm">
            <option value="">全部状态</option>
            <option value="draft">draft</option>
            <option value="active">active</option>
            <option value="archived">archived</option>
          </select>
          <select value={categoryId} onChange={(e) => setCategoryId(e.target.value)} className="rounded-lg border border-stone-300 px-3 py-2 text-sm">
            <option value="">全部分类</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>{category.name}</option>
            ))}
          </select>
          <button
            type="button"
            onClick={() => {
              if (page === 1) load();
              else setPage(1);
            }}
            className="rounded-lg bg-stone-900 px-3 py-2 text-sm text-white"
          >
            筛选
          </button>
        </div>
        <div className="mt-3 flex gap-2">
          <button type="button" onClick={handleBulkActive} className="rounded-lg border border-stone-300 px-3 py-1.5 text-sm text-stone-700">
            批量上架
          </button>
          <button type="button" onClick={handleBulkArchive} className="rounded-lg border border-stone-300 px-3 py-1.5 text-sm text-stone-700">
            批量归档
          </button>
        </div>
      </div>

      {error ? <p className="text-sm text-red-600">{error}</p> : null}
      <div className="overflow-hidden rounded-2xl border border-stone-200 bg-white">
        <table className="w-full text-sm">
          <thead className="bg-stone-50 text-left text-stone-600">
            <tr>
              <th className="px-3 py-3">#</th>
              <th className="px-3 py-3">商品</th>
              <th className="px-3 py-3">价格</th>
              <th className="px-3 py-3">库存</th>
              <th className="px-3 py-3">状态</th>
              <th className="px-3 py-3">更新时间</th>
              <th className="px-3 py-3">操作</th>
            </tr>
          </thead>
          <tbody>
            {data?.items.map((item) => (
              <tr key={item.id} className="border-t border-stone-100">
                <td className="px-3 py-3">
                  <input type="checkbox" checked={selectedIds.includes(item.id)} onChange={() => toggleItem(item)} />
                </td>
                <td className="px-3 py-3">
                  <div className="flex items-center gap-3">
                    {item.cover_image_asset?.media_kind === "video" ? (
                      <video
                        src={item.cover_image || "https://placehold.co/80x80"}
                        className="h-10 w-10 rounded-md object-cover"
                        muted
                        loop
                        playsInline
                      />
                    ) : (
                      <img src={item.cover_image || "https://placehold.co/80x80"} alt={item.name} className="h-10 w-10 rounded-md object-cover" />
                    )}
                    <div>
                      <p className="font-medium text-stone-800">{item.name}</p>
                      <p className="text-xs text-stone-500">{item.slug}</p>
                    </div>
                  </div>
                </td>
                <td className="px-3 py-3">¥{item.price}</td>
                <td className="px-3 py-3">{item.stock}</td>
                <td className="px-3 py-3"><StatusPill status={item.status} /></td>
                <td className="px-3 py-3 text-xs text-stone-500">{new Date(item.updated_at).toLocaleString()}</td>
                <td className="px-3 py-3">
                  <div className="flex gap-2">
                    <Link href={`/admin/products/${item.id}`} className="text-stone-700 hover:text-stone-900">编辑</Link>
                    <button type="button" onClick={() => handleDelete(item.id)} className="text-red-600 hover:text-red-700">
                      删除
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {data?.items.length === 0 ? <p className="px-4 py-8 text-center text-sm text-stone-500">暂无商品</p> : null}
      </div>
      <div className="flex items-center justify-end gap-2">
        <button disabled={page <= 1} onClick={() => setPage((v) => v - 1)} className="rounded-lg border border-stone-300 px-3 py-1.5 text-sm disabled:opacity-40">
          上一页
        </button>
        <span className="text-sm text-stone-600">{page} / {totalPages}</span>
        <button disabled={page >= totalPages} onClick={() => setPage((v) => v + 1)} className="rounded-lg border border-stone-300 px-3 py-1.5 text-sm disabled:opacity-40">
          下一页
        </button>
      </div>
    </AdminPageShell>
  );
}
