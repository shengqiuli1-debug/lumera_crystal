import { CategoryForm } from "@/components/admin/category-form";
import { AdminPageShell } from "@/components/admin/page-shell";

export default function NewCategoryPage() {
  return (
    <AdminPageShell title="新增分类" description="轻量填写，快速创建。">
      <CategoryForm />
    </AdminPageShell>
  );
}
