"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { CART_UPDATED_EVENT, getCart } from "@/lib/cart";

export function Navbar() {
  const [cartCount, setCartCount] = useState(0);
  const links = [
    { href: "/", label: "首页" },
    { href: "/products", label: "晶石商店" },
    { href: "/cart", label: "购物车" },
    { href: "/shop", label: "订单" },
    { href: "/categories/amethyst", label: "分类" },
    { href: "/blog", label: "灵感日志" },
    { href: "/about", label: "品牌" },
    { href: "/contact", label: "联系" }
  ];

  useEffect(() => {
    const syncCount = () => {
      const count = getCart().reduce((sum, item) => sum + item.quantity, 0);
      setCartCount(count);
    };

    syncCount();
    window.addEventListener("storage", syncCount);
    window.addEventListener(CART_UPDATED_EVENT, syncCount);
    return () => {
      window.removeEventListener("storage", syncCount);
      window.removeEventListener(CART_UPDATED_EVENT, syncCount);
    };
  }, []);

  return (
    <header className="sticky top-0 z-30 border-b border-mist/50 bg-ivory/80 backdrop-blur">
      <div className="mx-auto flex h-16 w-full max-w-7xl items-center justify-between px-4 md:px-8">
        <Link href="/" className="font-serif text-xl tracking-[0.2em] text-ink">
          LUMERA CRYSTAL
        </Link>
        <div className="relative md:hidden">
          <Link href="/cart" className="text-sm text-ink/80 hover:text-ink">
            购物车
          </Link>
          {cartCount > 0 ? (
            <span className="absolute -right-4 -top-2 rounded-full bg-ink px-1.5 py-0.5 text-[10px] leading-none text-ivory">
              {cartCount > 99 ? "99+" : cartCount}
            </span>
          ) : null}
        </div>
        <nav className="hidden gap-6 text-sm text-ink/80 md:flex">
          {links.map((item) => (
            <div key={item.href} className="relative">
              <Link href={item.href} className="hover:text-ink">
                {item.label}
              </Link>
              {item.href === "/cart" && cartCount > 0 ? (
                <span className="absolute -right-4 -top-2 rounded-full bg-ink px-1.5 py-0.5 text-[10px] leading-none text-ivory">
                  {cartCount > 99 ? "99+" : cartCount}
                </span>
              ) : null}
            </div>
          ))}
        </nav>
      </div>
    </header>
  );
}
