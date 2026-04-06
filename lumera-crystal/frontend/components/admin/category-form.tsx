"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { createAdminCategory, getAdminCategory, updateAdminCategory } from "@/lib/admin-api";

export function CategoryForm({ categoryId }: { categoryId?: number }) {
  const router = useRouter();
  const [form, setForm] = useState({
    name: "",
    slug: "",
    description: "",
    cover_image: "",
    sort_order: 0,
  });
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!categoryId) return;
    getAdminCategory(categoryId).then((item) => {
      setForm({
        name: item.name,
        slug: item.slug,
        description: item.description,
        cover_image: item.cover_image,
        sort_order: item.sort_order,
      });
    });
  }, [categoryId]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setMessage(null);
    try {
      if (categoryId) {
        await updateAdminCategory(categoryId, form);
      } else {
        await createAdminCategory(form);
      }
      setMessage("保存成功");
      setTimeout(() => router.push("/admin/categories"), 500);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "保存失败");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4 rounded-2xl border border-stone-200 bg-white p-5">
      <label className="block space-y-1 text-sm">
        <span className="text-stone-600">名称</span>
        <input className="w-full rounded-lg border border-stone-300 px-3 py-2" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
      </label>
      <label className="block space-y-1 text-sm">
        <span className="text-stone-600">Slug</span>
        <input className="w-full rounded-lg border border-stone-300 px-3 py-2" value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value })} required />
      </label>
      <label className="block space-y-1 text-sm">
        <span className="text-stone-600">描述</span>
        <textarea className="min-h-24 w-full rounded-lg border border-stone-300 px-3 py-2" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
      </label>
      <label className="block space-y-1 text-sm">
        <span className="text-stone-600">封面图 URL</span>
        <input className="w-full rounded-lg border border-stone-300 px-3 py-2" value={form.cover_image} onChange={(e) => setForm({ ...form, cover_image: e.target.value })} />
      </label>
      <label className="block space-y-1 text-sm">
        <span className="text-stone-600">排序</span>
        <input type="number" className="w-full rounded-lg border border-stone-300 px-3 py-2" value={form.sort_order} onChange={(e) => setForm({ ...form, sort_order: Number(e.target.value) })} />
      </label>
      <div className="flex items-center gap-3">
        {message ? <span className="text-sm text-stone-600">{message}</span> : null}
        <button type="button" className="rounded-lg border border-stone-300 px-3 py-2 text-sm" onClick={() => router.push("/admin/categories")}>
          取消
        </button>
        <button type="submit" disabled={saving} className="rounded-lg bg-stone-900 px-4 py-2 text-sm text-white disabled:opacity-60">
          {saving ? "保存中..." : "保存"}
        </button>
      </div>
    </form>
  );
}
