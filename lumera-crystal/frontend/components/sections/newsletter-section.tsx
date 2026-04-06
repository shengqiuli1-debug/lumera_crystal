"use client";

import { FormEvent, useState } from "react";

import { submitNewsletter } from "@/lib/api";

import { Button } from "../ui/button";
import { Input } from "../ui/input";

export function NewsletterSection() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState("");

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    try {
      await submitNewsletter({ email, source: "homepage" });
      setStatus("订阅成功，欢迎加入 LUMERA 内测名单。 ");
      setEmail("");
    } catch {
      setStatus("订阅失败，请稍后重试。 ");
    }
  };

  return (
    <section className="rounded-3xl border border-mist/70 bg-white/70 p-8">
      <p className="text-xs uppercase tracking-[0.2em] text-gold">Newsletter</p>
      <h3 className="mt-3 font-serif text-3xl">订阅每月灵感与新品预览</h3>
      <form onSubmit={onSubmit} className="mt-6 flex flex-col gap-3 md:flex-row">
        <Input required type="email" placeholder="输入邮箱" value={email} onChange={(e) => setEmail(e.target.value)} />
        <Button type="submit">订阅</Button>
      </form>
      {status ? <p className="mt-3 text-sm text-ink/70">{status}</p> : null}
    </section>
  );
}
