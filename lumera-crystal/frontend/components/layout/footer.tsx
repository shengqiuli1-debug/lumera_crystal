import Link from "next/link";

export function Footer() {
  return (
    <footer className="mt-20 border-t border-mist/60 bg-white/60">
      <div className="mx-auto grid w-full max-w-7xl gap-10 px-4 py-12 md:grid-cols-3 md:px-8">
        <div>
          <p className="font-serif text-lg tracking-[0.18em]">LUMERA CRYSTAL</p>
          <p className="mt-3 text-sm leading-6 text-ink/70">现代、安静、治愈、自然、轻奢。让每件晶石成为你日常节奏里的柔和光源。</p>
        </div>
        <div>
          <p className="mb-3 text-sm font-medium">探索</p>
          <div className="space-y-2 text-sm text-ink/75">
            <Link href="/products" className="block hover:text-ink">全部商品</Link>
            <Link href="/blog" className="block hover:text-ink">灵感日志</Link>
            <Link href="/about" className="block hover:text-ink">品牌故事</Link>
          </div>
        </div>
        <div>
          <p className="mb-3 text-sm font-medium">联系</p>
          <p className="text-sm text-ink/75">support@lumeracrystal.com</p>
          <p className="text-sm text-ink/75">上海 · 设计工作室</p>
        </div>
      </div>
    </footer>
  );
}
