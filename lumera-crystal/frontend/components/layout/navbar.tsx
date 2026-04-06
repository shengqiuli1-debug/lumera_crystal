import Link from "next/link";

const links = [
  { href: "/", label: "首页" },
  { href: "/products", label: "晶石商店" },
  { href: "/shop", label: "商城" },
  { href: "/categories/amethyst", label: "分类" },
  { href: "/blog", label: "灵感日志" },
  { href: "/about", label: "品牌" },
  { href: "/contact", label: "联系" }
];

export function Navbar() {
  return (
    <header className="sticky top-0 z-30 border-b border-mist/50 bg-ivory/80 backdrop-blur">
      <div className="mx-auto flex h-16 w-full max-w-7xl items-center justify-between px-4 md:px-8">
        <Link href="/" className="font-serif text-xl tracking-[0.2em] text-ink">
          LUMERA CRYSTAL
        </Link>
        <nav className="hidden gap-6 text-sm text-ink/80 md:flex">
          {links.map((item) => (
            <Link key={item.href} href={item.href} className="hover:text-ink">
              {item.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
