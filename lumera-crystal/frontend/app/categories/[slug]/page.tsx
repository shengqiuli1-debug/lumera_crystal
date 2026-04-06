import { ProductGrid } from "@/components/product/product-grid";
import { SectionTitle } from "@/components/shared/section-title";
import { getCategory, getProducts } from "@/lib/api";

export default async function CategoryPage({ params }: { params: { slug: string } }) {
  const [category, productsResp] = await Promise.all([
    getCategory(params.slug),
    getProducts({ category: params.slug, page_size: 12 })
  ]);

  return (
    <div className="space-y-8">
      <SectionTitle eyebrow="Category" title={category.name} description={category.description} />
      <ProductGrid products={productsResp.items} />
    </div>
  );
}
