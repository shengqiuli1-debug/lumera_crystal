import { AdminPageShell } from "@/components/admin/page-shell";
import { ProductForm } from "@/components/admin/product-form";

export default function NewProductPage() {
  return (
    <AdminPageShell title="新增商品" description="用分组表单快速完成一次完整录入。">
      <ProductForm />
    </AdminPageShell>
  );
}
