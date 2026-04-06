"use client";

import { useRouter, useSearchParams } from "next/navigation";

import { Input } from "@/components/ui/input";

export function FilterSidebar() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const setQuery = (key: string, value: string) => {
    const params = new URLSearchParams(searchParams.toString());
    if (!value) params.delete(key);
    else params.set(key, value);
    router.push(`/products?${params.toString()}`);
  };

  return (
    <aside className="space-y-4 rounded-3xl border border-mist/70 bg-white/70 p-4">
      <p className="text-sm font-medium">筛选</p>
      <Input placeholder="颜色，如 紫晶调" defaultValue={searchParams.get("color") ?? ""} onBlur={(e) => setQuery("color", e.target.value)} />
      <Input placeholder="寓意，如 平静" defaultValue={searchParams.get("intention") ?? ""} onBlur={(e) => setQuery("intention", e.target.value)} />
      <Input placeholder="最低价格" type="number" defaultValue={searchParams.get("min_price") ?? ""} onBlur={(e) => setQuery("min_price", e.target.value)} />
      <Input placeholder="最高价格" type="number" defaultValue={searchParams.get("max_price") ?? ""} onBlur={(e) => setQuery("max_price", e.target.value)} />
    </aside>
  );
}
