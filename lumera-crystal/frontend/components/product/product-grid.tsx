import { Product } from "@/types";

import { ProductCard } from "./product-card";

export function ProductGrid({ products }: { products: Product[] }) {
  if (!products.length) {
    return (
      <div className="rounded-3xl border border-dashed border-mist p-12 text-center text-sm text-ink/60">
        暂无符合筛选条件的商品，试试放宽筛选范围。
      </div>
    );
  }

  return (
    <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
      {products.map((product) => (
        <ProductCard key={product.id} product={product} />
      ))}
    </div>
  );
}
