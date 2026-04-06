import { AdminPageShell } from "@/components/admin/page-shell";
import { ProductForm } from "@/components/admin/product-form";

export default function EditProductPage({ params }: { params: { id: string } }) {
  return (
    <AdminPageShell title="编辑商品" description="信息拆分为多区块，降低来回滚动成本。">
      <ProductForm productId={Number(params.id)} />
    </AdminPageShell>
  );
}
