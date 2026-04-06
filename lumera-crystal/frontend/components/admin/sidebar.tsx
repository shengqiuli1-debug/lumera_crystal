"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Blocks, FileText, Gem, LayoutDashboard, Mail, Send, Settings } from "lucide-react";

import { cn } from "@/lib/utils";

const navItems = [
  { href: "/admin", label: "概览", icon: LayoutDashboard },
  { href: "/admin/products", label: "商品管理", icon: Gem },
  { href: "/admin/categories", label: "分类管理", icon: Blocks },
  { href: "/admin/posts", label: "博客管理", icon: FileText },
  { href: "/admin/messages", label: "联系留言", icon: Mail },
  { href: "/admin/newsletter", label: "Newsletter", icon: Send },
  { href: "/admin/settings", label: "设置", icon: Settings },
];

export function AdminSidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 shrink-0 border-r border-stone-200 bg-[#f8f6f1]">
      <div className="px-6 py-6">
        <p className="text-xs uppercase tracking-[0.2em] text-stone-500">LUMERA CRYSTAL</p>
        <h1 className="mt-2 text-lg font-semibold text-stone-800">商家后台</h1>
      </div>
      <nav className="space-y-1 px-3">
        {navItems.map((item) => {
          const isActive = item.href === "/admin" ? pathname === "/admin" : pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition",
                isActive ? "bg-white text-stone-900 shadow-soft" : "text-stone-600 hover:bg-white/70 hover:text-stone-900"
              )}
            >
              <Icon size={16} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
