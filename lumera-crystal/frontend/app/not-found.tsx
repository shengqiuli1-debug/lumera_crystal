import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex min-h-[55vh] flex-col items-center justify-center text-center">
      <p className="text-xs uppercase tracking-[0.2em] text-gold">404</p>
      <h1 className="mt-3 font-serif text-4xl">页面暂时走丢了</h1>
      <p className="mt-3 text-sm text-ink/70">你可以回到首页继续探索 LUMERA 的晶石世界。</p>
      <Link href="/" className="mt-6 rounded-full border border-ink px-5 py-2 text-sm hover:bg-ink hover:text-ivory">
        返回首页
      </Link>
    </div>
  );
}
