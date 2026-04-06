"use client";

import { useRouter, useSearchParams } from "next/navigation";

import { Input } from "@/components/ui/input";

export function SearchBar() {
  const router = useRouter();
  const searchParams = useSearchParams();

  return (
    <Input
      defaultValue={searchParams.get("search") ?? ""}
      placeholder="搜索商品名、描述、晶石类型"
      onKeyDown={(event) => {
        if (event.key !== "Enter") return;
        const params = new URLSearchParams(searchParams.toString());
        const value = (event.target as HTMLInputElement).value;
        if (!value) params.delete("search");
        else params.set("search", value);
        router.push(`/products?${params.toString()}`);
      }}
    />
  );
}
