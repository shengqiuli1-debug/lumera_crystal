"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { AdminPageShell } from "@/components/admin/page-shell";
import { AdminApiError, getAdminMessages, markAdminMessageRead, replyAdminMessage } from "@/lib/admin-api";
import type { AdminMessage, AdminMessageListResponse } from "@/types/admin";

export default function AdminMessagesPage() {
  const [data, setData] = useState<AdminMessageListResponse | null>(null);
  const [focus, setFocus] = useState<AdminMessage | null>(null);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [readFilter, setReadFilter] = useState("");
  const [replyText, setReplyText] = useState("");
  const [replyNotice, setReplyNotice] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [replySending, setReplySending] = useState(false);
  const [cooldownUntil, setCooldownUntil] = useState(0);
  const [nowTs, setNowTs] = useState(Date.now());

  const cooldownSeconds = Math.max(0, Math.ceil((cooldownUntil - nowTs) / 1000));

  const load = useCallback(async () => {
    const result = await getAdminMessages({
      page,
      page_size: 20,
      search: search || undefined,
      is_read: readFilter === "" ? undefined : readFilter === "true",
    });
    setData(result);
  }, [page, readFilter, search]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    setReplyText("");
    setReplyNotice(null);
  }, [focus?.id]);

  useEffect(() => {
    if (cooldownUntil <= Date.now()) return;
    const timer = window.setInterval(() => setNowTs(Date.now()), 300);
    return () => window.clearInterval(timer);
  }, [cooldownUntil]);

  const totalPages = useMemo(() => (data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1), [data]);

  async function toggleRead(item: AdminMessage) {
    const updated = await markAdminMessageRead(item.id, !item.is_read);
    setFocus((prev) => (prev?.id === updated.id ? updated : prev));
    await load();
  }

  async function handleReply() {
    if (!focus || replySending || cooldownSeconds > 0) return;
    const content = replyText.trim();
    if (!content) {
      setReplyNotice({ type: "error", text: "请先填写回复内容。" });
      return;
    }

    setReplySending(true);
    setReplyNotice(null);
    try {
      const updated = await replyAdminMessage(focus.id, content);
      setFocus(updated);
      setReplyText("");
      setReplyNotice({ type: "success", text: "回复已发送，消息已自动标记为已回复。" });
      setCooldownUntil(Date.now() + 3500);
      await load();
    } catch (error) {
      if (error instanceof AdminApiError) {
        setReplyNotice({ type: "error", text: error.message });
      } else {
        setReplyNotice({ type: "error", text: error instanceof Error ? error.message : "发送回复失败" });
      }
    } finally {
      setReplySending(false);
    }
  }

  function renderStatus(item: AdminMessage) {
    if (item.auto_reply_status === "replied") return "已回复";
    if (item.is_read) return "已读";
    return "未读";
  }

  return (
    <AdminPageShell title="联系留言" description="集中查看咨询、标记已读，并直接回复用户邮件。">
      <div className="flex gap-2">
        <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="搜索姓名/邮箱/主题" className="w-64 rounded-lg border border-stone-300 px-3 py-2 text-sm" />
        <select value={readFilter} onChange={(e) => setReadFilter(e.target.value)} className="rounded-lg border border-stone-300 px-3 py-2 text-sm">
          <option value="">全部</option>
          <option value="false">未读</option>
          <option value="true">已读</option>
        </select>
        <button
          type="button"
          onClick={() => {
            if (page === 1) load();
            else setPage(1);
          }}
          className="rounded-lg border border-stone-300 px-3 py-2 text-sm"
        >
          筛选
        </button>
      </div>
      <div className="grid gap-4 lg:grid-cols-[1fr_360px]">
        <div className="overflow-hidden rounded-2xl border border-stone-200 bg-white">
          <table className="w-full text-sm">
            <thead className="bg-stone-50 text-left text-stone-600">
              <tr>
                <th className="px-3 py-3">姓名</th>
                <th className="px-3 py-3">主题</th>
                <th className="px-3 py-3">状态</th>
                <th className="px-3 py-3">时间</th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((item) => (
                <tr key={item.id} className="cursor-pointer border-t border-stone-100 hover:bg-stone-50" onClick={() => setFocus(item)}>
                  <td className="px-3 py-3">{item.name}</td>
                  <td className="px-3 py-3">{item.subject}</td>
                  <td className="px-3 py-3">
                    <span
                      className={`text-xs ${
                        item.auto_reply_status === "replied"
                          ? "text-emerald-600"
                          : item.is_read
                            ? "text-stone-500"
                            : "text-amber-600"
                      }`}
                    >
                      {renderStatus(item)}
                    </span>
                  </td>
                  <td className="px-3 py-3 text-xs text-stone-500">{new Date(item.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {data?.items.length === 0 ? <p className="px-4 py-8 text-center text-sm text-stone-500">暂无留言</p> : null}
        </div>
        <aside className="rounded-2xl border border-stone-200 bg-white p-4">
          {focus ? (
            <div className="space-y-3">
              <div>
                <p className="text-xs text-stone-500">发件人</p>
                <p className="text-sm text-stone-800">{focus.name} · {focus.email}</p>
              </div>
              <div>
                <p className="text-xs text-stone-500">主题</p>
                <p className="text-sm text-stone-800">{focus.subject}</p>
              </div>
              <div>
                <p className="text-xs text-stone-500">内容</p>
                <p className="whitespace-pre-wrap text-sm text-stone-700">{focus.message}</p>
              </div>
              <div className="rounded-xl border border-stone-200 bg-stone-50/80 p-3">
                <p className="text-xs text-stone-500">回复用户</p>
                <textarea
                  className="mt-2 min-h-24 w-full rounded-lg border border-stone-300 px-3 py-2 text-sm"
                  value={replyText}
                  onChange={(event) => setReplyText(event.target.value)}
                  placeholder="输入给用户的回复内容，发送后会自动邮件通知。"
                />
                {replyNotice ? (
                  <p className={`mt-2 text-xs ${replyNotice.type === "success" ? "text-emerald-700" : "text-red-600"}`}>{replyNotice.text}</p>
                ) : null}
                <button
                  type="button"
                  onClick={handleReply}
                  disabled={replySending || cooldownSeconds > 0 || !replyText.trim()}
                  className="mt-2 rounded-lg bg-stone-900 px-3 py-2 text-sm text-white disabled:cursor-not-allowed disabled:opacity-55"
                >
                  {replySending ? "发送中..." : cooldownSeconds > 0 ? `${cooldownSeconds}s 后可再次发送` : "发送回复"}
                </button>
              </div>
              <button type="button" onClick={() => toggleRead(focus)} className="rounded-lg border border-stone-300 px-3 py-2 text-sm">
                标记为{focus.is_read ? "未读" : "已读"}
              </button>
            </div>
          ) : (
            <p className="text-sm text-stone-500">选择一条留言查看详情</p>
          )}
        </aside>
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
