"use client";

import { useMemo, useState } from "react";
import { Send } from "lucide-react";

import { sendSupportChat, type SupportChatResult } from "@/lib/support-chat";
import { cn } from "@/lib/utils";

const quickPrompts = [
  "发邮件给 li@example.com，告诉他明天下午3点开会，语气正式一点",
  "发邮件给 王总，主题是项目延期说明，内容是由于接口联调问题，预计延期到周五",
  "发邮件给 test@example.com，内容：报价单已更新，请查收",
];

type ChatItem = {
  id: string;
  role: "agent" | "operator";
  content: string;
  meta?: SupportChatResult | null;
};

export function SupportChat() {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [history, setHistory] = useState<ChatItem[]>([
    {
      id: "intro",
      role: "agent",
      content: "这里是客服对话台。默认会给出客服回复，若以“发邮件给…”开头则进入邮件发送流程。",
    },
  ]);
  const canSend = input.trim().length > 0 && !loading;

  const promptTips = useMemo(() => {
    return "示例：发邮件给 王总，主题是项目延期说明，内容是由于接口联调问题，预计延期到周五";
  }, []);

  async function handleSend() {
    if (!canSend) return;
    const message = input.trim();
    const entry: ChatItem = {
      id: `${Date.now()}-operator`,
      role: "operator",
      content: message,
    };

    setHistory((prev) => [...prev, entry]);
    setInput("");
    setLoading(true);

    try {
      const result = await sendSupportChat(message, conversationId);
      if (result.conversation_id && result.conversation_id !== conversationId) {
        setConversationId(result.conversation_id);
      }
      const responseContent = renderResult(result);
      setHistory((prev) => [
        ...prev,
        {
          id: `${Date.now()}-agent`,
          role: "agent",
          content: responseContent,
          meta: result,
        },
      ]);
    } catch (error) {
      const messageText = error instanceof Error ? error.message : "请求失败";
      setHistory((prev) => [
        ...prev,
        {
          id: `${Date.now()}-agent`,
          role: "agent",
          content: `发送失败：${messageText}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="rounded-3xl border border-stone-200 bg-white/80 p-6 shadow-sm">
      <div className="flex items-start justify-between gap-6">
        <div>
          <p className="text-xs uppercase tracking-[0.28em] text-stone-400">Support Console</p>
          <h2 className="mt-2 text-2xl font-semibold text-stone-900">客服对话框</h2>
          <p className="mt-2 max-w-2xl text-sm text-stone-600">
            仅供客服使用。普通问题会生成回复，以“发邮件给…”开头则解析收件人/主题/正文并发送邮件。
          </p>
        </div>
        <span className="rounded-full border border-stone-200 bg-stone-100 px-3 py-1 text-xs text-stone-600">仅客服</span>
      </div>

      <div className="mt-6 space-y-4">
        <div className="flex flex-wrap gap-2">
          {quickPrompts.map((prompt) => (
            <button
              type="button"
              key={prompt}
              onClick={() => setInput(prompt)}
              className="rounded-full border border-stone-200 bg-white px-3 py-1 text-xs text-stone-600 hover:border-stone-300 hover:text-stone-900"
            >
              {prompt}
            </button>
          ))}
        </div>

        <div className="max-h-[420px] space-y-3 overflow-y-auto rounded-2xl border border-stone-200 bg-[#fbfaf8] p-4">
          {history.map((item) => (
            <div
              key={item.id}
              className={cn(
                "rounded-2xl px-4 py-3 text-sm",
                item.role === "operator"
                  ? "ml-auto max-w-[80%] bg-stone-900 text-white"
                  : "mr-auto max-w-[80%] bg-white text-stone-800 shadow-sm"
              )}
            >
              <p className="whitespace-pre-wrap leading-6">{item.content}</p>
              {item.meta?.mail ? (
                <div className="mt-3 rounded-xl border border-stone-200 bg-stone-50 p-3 text-xs text-stone-600">
                  <p>收件人：{item.meta.mail.to}</p>
                  <p>主题：{item.meta.mail.subject}</p>
                  <p>解析方式：{item.meta.mail.parsed_by}</p>
                </div>
              ) : null}
            </div>
          ))}
        </div>

        <div className="space-y-2">
          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder={promptTips}
            className="h-28 w-full resize-none rounded-2xl border border-stone-200 bg-white px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-stone-300"
          />
          <div className="flex items-center justify-between text-xs text-stone-500">
            <p>普通提问会生成回复，发邮件请以“发邮件给”开头。</p>
            <button
              type="button"
              onClick={handleSend}
              disabled={!canSend}
              className={cn(
                "inline-flex items-center gap-2 rounded-full px-4 py-2 text-xs font-medium",
                canSend
                  ? "bg-stone-900 text-white hover:bg-stone-800"
                  : "bg-stone-200 text-stone-500"
              )}
            >
              <Send size={14} />
              {loading ? "发送中..." : "发送邮件"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function renderResult(result: SupportChatResult) {
  if (result.status === "sent") {
    return "已发送邮件。你可以在下方查看解析出的收件人和主题。";
  }
  if (result.status === "reply") {
    return result.reply ?? "已生成回复。";
  }
  return `发送失败：${result.error?.message ?? result.message}`;
}
