"use client";

import { useRouter } from "next/navigation";
import { LogOut } from "lucide-react";

import { clearAdminAuth, getAdminEmail } from "@/lib/admin-auth";
import { adminLogout } from "@/lib/admin-api";

export function AdminHeader() {
  const router = useRouter();
  const adminEmail = getAdminEmail();

  async function handleLogout() {
    try {
      await adminLogout();
    } catch {
      // ignore
    } finally {
      clearAdminAuth();
      router.replace("/admin/login");
    }
  }

  return (
    <header className="flex h-16 items-center justify-between border-b border-stone-200 bg-white/90 px-6 backdrop-blur">
      <div>
        <p className="text-xs uppercase tracking-[0.12em] text-stone-500">Merchant Console</p>
        <p className="text-sm text-stone-700">轻量、安静、可持续维护</p>
      </div>
      <div className="flex items-center gap-3">
        <p className="text-sm text-stone-600">{adminEmail ?? "Admin"}</p>
        <button
          type="button"
          onClick={handleLogout}
          className="inline-flex items-center gap-1 rounded-lg border border-stone-300 px-3 py-1.5 text-sm text-stone-700 transition hover:bg-stone-100"
        >
          <LogOut size={14} />
          退出
        </button>
      </div>
    </header>
  );
}
