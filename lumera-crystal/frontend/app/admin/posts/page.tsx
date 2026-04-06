"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { AdminPageShell } from "@/components/admin/page-shell";
import { StatusPill } from "@/components/admin/status-pill";
import { deleteAdminPost, getAdminPosts } from "@/lib/admin-api";
import type { AdminPostListResponse } from "@/types/admin";

export default function AdminPostsPage() {
  const [data, setData] = useState<AdminPostListResponse | null>(null);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      const result = await getAdminPosts({
        page,
        page_size: 12,
        search: search || undefined,
        status: status || undefined,
      });
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载失败");
    }
  }, [page, search, status]);

  useEffect(() => {
    load();
  }, [load]);

  async function remove(id: number) {
    if (!confirm("确认删除该博客？")) return;
    await deleteAdminPost(id);
    await load();
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;

  return (
    <AdminPageShell
      title="博客管理"
      description="支持草稿与发布状态切换，后续可平滑接富文本编辑器。"
      actions={
        <Link href="/admin/posts/new" className="rounded-lg bg-stone-900 px-3 py-2 text-sm text-white">
          新增博客
        </Link>
      }
    >
      <div className="flex gap-2">
        <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="搜索标题或 slug" className="w-64 rounded-lg border border-stone-300 px-3 py-2 text-sm" />
        <select value={status} onChange={(e) => setStatus(e.target.value)} className="rounded-lg border border-stone-300 px-3 py-2 text-sm">
          <option value="">全部状态</option>
          <option value="draft">draft</option>
          <option value="published">published</option>
          <option value="archived">archived</option>
        </select>
        <button
          type="button"
          onClick={() => {
            if (page === 1) load();
            else setPage(1);
          }}
          className="rounded-lg border border-stone-300 px-3 py-2 text-sm text-stone-700"
        >
          筛选
        </button>
      </div>
      {error ? <p className="text-sm text-red-600">{error}</p> : null}
      <div className="overflow-hidden rounded-2xl border border-stone-200 bg-white">
        <table className="w-full text-sm">
          <thead className="bg-stone-50 text-left text-stone-600">
            <tr>
              <th className="px-3 py-3">标题</th>
              <th className="px-3 py-3">Slug</th>
              <th className="px-3 py-3">状态</th>
              <th className="px-3 py-3">更新时间</th>
              <th className="px-3 py-3">操作</th>
            </tr>
          </thead>
          <tbody>
            {data?.items.map((item) => (
              <tr key={item.id} className="border-t border-stone-100">
                <td className="px-3 py-3">
                  <div className="flex items-center gap-3">
                    {item.cover_image ? (
                      <img src={item.cover_image} alt={item.title} className="h-10 w-10 rounded-md object-cover" />
                    ) : (
                      <div className="h-10 w-10 rounded-md bg-stone-100" />
                    )}
                    <span>{item.title}</span>
                  </div>
                </td>
                <td className="px-3 py-3 text-stone-500">{item.slug}</td>
                <td className="px-3 py-3"><StatusPill status={item.status} /></td>
                <td className="px-3 py-3 text-xs text-stone-500">{new Date(item.updated_at).toLocaleString()}</td>
                <td className="px-3 py-3">
                  <div className="flex gap-2">
                    <Link href={`/admin/posts/${item.id}`} className="text-stone-700">编辑</Link>
                    <button type="button" className="text-red-600" onClick={() => remove(item.id)}>
                      删除
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {data?.items.length === 0 ? <p className="px-4 py-8 text-center text-sm text-stone-500">暂无博客</p> : null}
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
