"use client";

export default function ErrorPage({ reset }: { reset: () => void }) {
  return (
    <div className="rounded-3xl border border-mist/70 bg-white/80 p-8 text-center">
      <h2 className="font-serif text-3xl">页面加载失败</h2>
      <p className="mt-3 text-sm text-ink/70">网络波动或服务暂时不可用，请稍后重试。</p>
      <button className="mt-6 rounded-full border border-ink px-5 py-2 text-sm" onClick={reset}>
        重新加载
      </button>
    </div>
  );
}
