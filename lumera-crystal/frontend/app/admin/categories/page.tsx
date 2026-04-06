"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { AdminPageShell } from "@/components/admin/page-shell";
import { deleteAdminCategory, getAdminCategories } from "@/lib/admin-api";
import type { AdminCategory } from "@/types/admin";

export default function AdminCategoriesPage() {
  const [items, setItems] = useState<AdminCategory[]>([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setItems(await getAdminCategories(search || undefined));
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载失败");
    }
  }, [search]);

  useEffect(() => {
    load();
  }, [load]);

  async function remove(id: number) {
    if (!confirm("确认删除该分类？")) return;
    try {
      await deleteAdminCategory(id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "删除失败");
    }
  }

  return (
    <AdminPageShell
      title="分类管理"
      description="维护商品分类与排序。"
      actions={
        <Link href="/admin/categories/new" className="rounded-lg bg-stone-900 px-3 py-2 text-sm text-white">
          新增分类
        </Link>
      }
    >
      <div className="flex gap-2">
        <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="搜索分类名或 slug" className="w-64 rounded-lg border border-stone-300 px-3 py-2 text-sm" />
        <button type="button" onClick={load} className="rounded-lg border border-stone-300 px-3 py-2 text-sm text-stone-700">
          搜索
        </button>
      </div>
      {error ? <p className="text-sm text-red-600">{error}</p> : null}
      <div className="overflow-hidden rounded-2xl border border-stone-200 bg-white">
        <table className="w-full text-sm">
          <thead className="bg-stone-50 text-left text-stone-600">
            <tr>
              <th className="px-3 py-3">名称</th>
              <th className="px-3 py-3">Slug</th>
              <th className="px-3 py-3">排序</th>
              <th className="px-3 py-3">更新时间</th>
              <th className="px-3 py-3">操作</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id} className="border-t border-stone-100">
                <td className="px-3 py-3">{item.name}</td>
                <td className="px-3 py-3 text-stone-500">{item.slug}</td>
                <td className="px-3 py-3">{item.sort_order}</td>
                <td className="px-3 py-3 text-xs text-stone-500">{new Date(item.updated_at).toLocaleString()}</td>
                <td className="px-3 py-3">
                  <div className="flex gap-2">
                    <Link href={`/admin/categories/${item.id}`} className="text-stone-700">编辑</Link>
                    <button type="button" className="text-red-600" onClick={() => remove(item.id)}>
                      删除
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 ? <p className="px-4 py-8 text-center text-sm text-stone-500">暂无分类</p> : null}
      </div>
    </AdminPageShell>
  );
}
