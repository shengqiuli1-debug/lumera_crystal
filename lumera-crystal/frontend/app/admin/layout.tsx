"use client";

import { usePathname } from "next/navigation";

import { AdminHeader } from "@/components/admin/header";
import { AdminSidebar } from "@/components/admin/sidebar";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isLogin = pathname === "/admin/login";

  if (isLogin) {
    return <div className="min-h-screen bg-[#f3f1ec]">{children}</div>;
  }

  return (
    <div className="min-h-screen bg-[#f3f1ec] text-stone-900">
      <div className="flex min-h-screen">
        <AdminSidebar />
        <div className="flex min-w-0 flex-1 flex-col">
          <AdminHeader />
          <main className="flex-1">{children}</main>
        </div>
      </div>
    </div>
  );
}
