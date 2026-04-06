import { CategoryForm } from "@/components/admin/category-form";
import { AdminPageShell } from "@/components/admin/page-shell";

export default function EditCategoryPage({ params }: { params: { id: string } }) {
  return (
    <AdminPageShell title="编辑分类" description="调整命名、排序和封面图。">
      <CategoryForm categoryId={Number(params.id)} />
    </AdminPageShell>
  );
}
