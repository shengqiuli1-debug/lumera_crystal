import { FilterSidebar } from "@/components/product/filter-sidebar";
import { ProductGrid } from "@/components/product/product-grid";
import { SearchBar } from "@/components/product/search-bar";
import { SectionTitle } from "@/components/shared/section-title";
import { getProducts } from "@/lib/api";

export default async function ProductsPage({ searchParams }: { searchParams: Record<string, string | undefined> }) {
  const productsResp = await getProducts({
    page: searchParams.page,
    page_size: searchParams.page_size ?? 12,
    category: searchParams.category,
    min_price: searchParams.min_price,
    max_price: searchParams.max_price,
    color: searchParams.color,
    intention: searchParams.intention,
    search: searchParams.search
  });

  return (
    <div className="space-y-8">
      <SectionTitle eyebrow="Shop" title="晶石商店" description="筛选你当前真正需要的能量风格。" />
      <SearchBar />
      <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
        <FilterSidebar />
        <ProductGrid products={productsResp.items} />
      </div>
    </div>
  );
}
