"use client";

import { FormEvent, useEffect, useRef, useState } from "react";

import { submitContact } from "@/lib/api";

import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Textarea } from "../ui/textarea";

export function ContactForm() {
  const [status, setStatus] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [toast, setToast] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [cooldownUntil, setCooldownUntil] = useState(0);
  const [nowTs, setNowTs] = useState(Date.now());
  const toastTimerRef = useRef<number | null>(null);

  const cooldownSeconds = Math.max(0, Math.ceil((cooldownUntil - nowTs) / 1000));

  useEffect(() => {
    if (cooldownUntil <= Date.now()) return;
    const timer = window.setInterval(() => setNowTs(Date.now()), 250);
    return () => window.clearInterval(timer);
  }, [cooldownUntil]);

  useEffect(() => {
    return () => {
      if (toastTimerRef.current) window.clearTimeout(toastTimerRef.current);
    };
  }, []);

  function showToast(type: "success" | "error", text: string) {
    setToast({ type, text });
    if (toastTimerRef.current) window.clearTimeout(toastTimerRef.current);
    toastTimerRef.current = window.setTimeout(() => setToast(null), 2600);
  }

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (submitting || cooldownSeconds > 0) return;
    const formData = new FormData(event.currentTarget);
    setSubmitting(true);
    setStatus("");
    try {
      const result = await submitContact({
        name: String(formData.get("name") || ""),
        email: String(formData.get("email") || ""),
        subject: "网站咨询",
        message: String(formData.get("question") || "")
      });
      if (result.auto_reply_status === "sent") {
        setStatus("我们已收到你的问题，并已发送自动回执邮件，请注意查收。");
      } else {
        setStatus("我们已收到你的问题并成功记录，当前邮件通道繁忙，我们会尽快人工回复。");
      }
      showToast("success", "发送成功，我们已收到你的消息。");
      setCooldownUntil(Date.now() + 3500);
      event.currentTarget.reset();
    } catch (error) {
      const message = error instanceof Error ? error.message : "提交失败，请稍后再试。";
      setStatus(message);
      showToast("error", message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <form onSubmit={onSubmit} className="space-y-4 rounded-3xl border border-mist/70 bg-white/80 p-6">
        <Input name="name" required placeholder="你的名字" />
        <Input name="email" required type="email" placeholder="邮箱" />
        <Textarea name="question" required rows={5} placeholder="请输入你的问题（例如：预算、颜色偏好、佩戴场景）" />
        <Button type="submit" disabled={submitting || cooldownSeconds > 0}>
          {submitting ? "提交中..." : cooldownSeconds > 0 ? `${cooldownSeconds}s 后可再次发送` : "发送消息"}
        </Button>
        {status ? <p className="text-sm text-ink/70">{status}</p> : null}
      </form>

      {toast ? (
        <div className="fixed bottom-6 right-6 z-50 max-w-sm rounded-2xl border border-stone-200 bg-white px-4 py-3 shadow-soft">
          <p className={`text-sm ${toast.type === "success" ? "text-emerald-700" : "text-red-600"}`}>{toast.text}</p>
        </div>
      ) : null}
    </>
  );
}
