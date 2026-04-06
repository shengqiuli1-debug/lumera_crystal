"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AdminPageShell } from "@/components/admin/page-shell";
import { StatusPill } from "@/components/admin/status-pill";
import { getDashboardOverview } from "@/lib/admin-api";
import type { DashboardOverviewResponse } from "@/types/admin";

export default function AdminDashboardPage() {
  const [data, setData] = useState<DashboardOverviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDashboardOverview()
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : "加载失败"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <AdminPageShell
      title="后台概览"
      description="今天需要处理什么，一眼可见。"
      actions={
        <div className="flex gap-2">
          <Link href="/admin/products/new" className="rounded-lg bg-stone-900 px-3 py-2 text-sm text-white">
            新增商品
          </Link>
          <Link href="/admin/posts/new" className="rounded-lg border border-stone-300 px-3 py-2 text-sm text-stone-700">
            新增博客
          </Link>
        </div>
      }
    >
      {loading ? <p className="text-sm text-stone-500">加载中...</p> : null}
      {error ? <p className="text-sm text-red-600">{error}</p> : null}
      {data ? (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
            {data.stats.map((stat) => (
              <div key={stat.label} className="rounded-2xl border border-stone-200 bg-white p-4">
                <p className="text-xs text-stone-500">{stat.label}</p>
                <p className="mt-2 text-2xl font-semibold text-stone-900">{stat.value}</p>
              </div>
            ))}
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <div className="rounded-2xl border border-stone-200 bg-white p-4">
              <h3 className="text-sm font-semibold text-stone-800">最近更新商品</h3>
              <div className="mt-3 space-y-2">
                {data.recent_products.map((item) => (
                  <div key={item.id} className="flex items-center justify-between rounded-xl border border-stone-100 px-3 py-2">
                    <Link href={`/admin/products/${item.id}`} className="text-sm text-stone-800 hover:text-stone-950">
                      {item.name}
                    </Link>
                    <StatusPill status={item.status} />
                  </div>
                ))}
              </div>
            </div>
            <div className="rounded-2xl border border-stone-200 bg-white p-4">
              <h3 className="text-sm font-semibold text-stone-800">最新留言</h3>
              <div className="mt-3 space-y-2">
                {data.latest_messages.map((item) => (
                  <Link
                    key={item.id}
                    href={`/admin/messages?focus=${item.id}`}
                    className="block rounded-xl border border-stone-100 px-3 py-2 hover:bg-stone-50"
                  >
                    <div className="flex items-center justify-between">
                      <p className="text-sm text-stone-800">{item.name}</p>
                      <span className={`text-xs ${item.is_read ? "text-stone-400" : "text-amber-600"}`}>
                        {item.is_read ? "已读" : "未读"}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-stone-500">{item.subject}</p>
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </AdminPageShell>
  );
}
