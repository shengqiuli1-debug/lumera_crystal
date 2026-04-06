"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { AdminApiError, createAdminPost, getAdminPost, updateAdminPost, uploadAdminImage } from "@/lib/admin-api";
import type { AdminPostStatus } from "@/types/admin";

type PostFormState = {
  title: string;
  slug: string;
  excerpt: string;
  cover_image: string;
  content: string;
  author: string;
  published_at: string;
  tags: string;
  seo_title: string;
  seo_description: string;
  status: AdminPostStatus;
};

export function PostForm({ postId }: { postId?: number }) {
  const router = useRouter();
  const [form, setForm] = useState<PostFormState>({
    title: "",
    slug: "",
    excerpt: "",
    cover_image: "",
    content: "",
    author: "LUMERA 编辑部",
    published_at: "",
    tags: "",
    seo_title: "",
    seo_description: "",
    status: "draft",
  });
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  async function onUploadCover(file?: File | null) {
    if (!file) return;
    setUploading(true);
    setMessage(null);
    try {
      const uploaded = await uploadAdminImage(file);
      setForm((prev) => ({ ...prev, cover_image: uploaded.url }));
      setMessage("封面图上传成功");
    } catch (error) {
      if (error instanceof AdminApiError) {
        setMessage(error.message);
      } else {
        setMessage(error instanceof Error ? error.message : "封面图上传失败");
      }
    } finally {
      setUploading(false);
    }
  }

  useEffect(() => {
    if (!postId) return;
    getAdminPost(postId).then((item) => {
      setForm({
        title: item.title,
        slug: item.slug,
        excerpt: item.excerpt,
        cover_image: item.cover_image,
        content: item.content,
        author: item.author,
        published_at: item.published_at ? item.published_at.slice(0, 16) : "",
        tags: item.tags.join(","),
        seo_title: item.seo_title,
        seo_description: item.seo_description,
        status: item.status,
      });
    });
  }, [postId]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setMessage(null);
    try {
      const payload = {
        ...form,
        tags: form.tags
          .split(",")
          .map((tag) => tag.trim())
          .filter(Boolean),
        published_at: form.published_at ? new Date(form.published_at).toISOString() : undefined,
      };
      if (postId) {
        await updateAdminPost(postId, payload);
      } else {
        await createAdminPost(payload);
      }
      setMessage("保存成功");
      setTimeout(() => router.push("/admin/posts"), 500);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "保存失败");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4 rounded-2xl border border-stone-200 bg-white p-5">
      <div className="grid gap-4 lg:grid-cols-2">
        <label className="space-y-1 text-sm">
          <span className="text-stone-600">标题</span>
          <input className="w-full rounded-lg border border-stone-300 px-3 py-2" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
        </label>
        <label className="space-y-1 text-sm">
          <span className="text-stone-600">Slug</span>
          <input className="w-full rounded-lg border border-stone-300 px-3 py-2" value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value })} required />
        </label>
      </div>
      <label className="block space-y-1 text-sm">
        <span className="text-stone-600">摘要</span>
        <textarea className="min-h-16 w-full rounded-lg border border-stone-300 px-3 py-2" value={form.excerpt} onChange={(e) => setForm({ ...form, excerpt: e.target.value })} />
      </label>
      <label className="block space-y-1 text-sm">
        <span className="text-stone-600">封面图 URL</span>
        <input className="w-full rounded-lg border border-stone-300 px-3 py-2" value={form.cover_image} onChange={(e) => setForm({ ...form, cover_image: e.target.value })} />
        <input
          type="file"
          accept="image/jpeg,image/png,image/webp,image/gif"
          onChange={(e) => onUploadCover(e.target.files?.[0])}
          disabled={uploading}
        />
        {form.cover_image ? (
          <div className="mt-2 overflow-hidden rounded-xl border border-stone-200">
            <img src={form.cover_image} alt={form.title || "博客封面"} className="h-36 w-full object-cover" />
          </div>
        ) : null}
      </label>
      <label className="block space-y-1 text-sm">
        <span className="text-stone-600">正文（后续可替换富文本）</span>
        <textarea className="min-h-72 w-full rounded-lg border border-stone-300 px-3 py-2" value={form.content} onChange={(e) => setForm({ ...form, content: e.target.value })} />
      </label>
      <div className="grid gap-4 lg:grid-cols-3">
        <label className="space-y-1 text-sm">
          <span className="text-stone-600">作者</span>
          <input className="w-full rounded-lg border border-stone-300 px-3 py-2" value={form.author} onChange={(e) => setForm({ ...form, author: e.target.value })} />
        </label>
        <label className="space-y-1 text-sm">
          <span className="text-stone-600">发布时间</span>
          <input type="datetime-local" className="w-full rounded-lg border border-stone-300 px-3 py-2" value={form.published_at} onChange={(e) => setForm({ ...form, published_at: e.target.value })} />
        </label>
        <label className="space-y-1 text-sm">
          <span className="text-stone-600">状态</span>
          <select
            className="w-full rounded-lg border border-stone-300 px-3 py-2"
            value={form.status}
            onChange={(e) => setForm({ ...form, status: e.target.value as AdminPostStatus })}
          >
            <option value="draft">draft</option>
            <option value="published">published</option>
            <option value="archived">archived</option>
          </select>
        </label>
      </div>
      <label className="block space-y-1 text-sm">
        <span className="text-stone-600">标签（逗号分隔）</span>
        <input className="w-full rounded-lg border border-stone-300 px-3 py-2" value={form.tags} onChange={(e) => setForm({ ...form, tags: e.target.value })} />
      </label>
      <div className="grid gap-4 lg:grid-cols-2">
        <label className="space-y-1 text-sm">
          <span className="text-stone-600">SEO 标题</span>
          <input className="w-full rounded-lg border border-stone-300 px-3 py-2" value={form.seo_title} onChange={(e) => setForm({ ...form, seo_title: e.target.value })} />
        </label>
        <label className="space-y-1 text-sm">
          <span className="text-stone-600">SEO 描述</span>
          <input className="w-full rounded-lg border border-stone-300 px-3 py-2" value={form.seo_description} onChange={(e) => setForm({ ...form, seo_description: e.target.value })} />
        </label>
      </div>
      <div className="flex items-center gap-3">
        {message ? <span className="text-sm text-stone-600">{message}</span> : null}
        <button type="button" onClick={() => router.push("/admin/posts")} className="rounded-lg border border-stone-300 px-3 py-2 text-sm">
          取消
        </button>
        <button type="submit" disabled={saving || uploading} className="rounded-lg bg-stone-900 px-4 py-2 text-sm text-white disabled:opacity-60">
          {saving ? "保存中..." : uploading ? "上传中..." : "保存"}
        </button>
      </div>
    </form>
  );
}
