import { AdminPageShell } from "@/components/admin/page-shell";
import { PostForm } from "@/components/admin/post-form";

export default function NewPostPage() {
  return (
    <AdminPageShell title="新增博客" description="围绕品牌气质持续输出内容。">
      <PostForm />
    </AdminPageShell>
  );
}
