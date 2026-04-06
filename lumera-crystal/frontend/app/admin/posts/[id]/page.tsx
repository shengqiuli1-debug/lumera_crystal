import { AdminPageShell } from "@/components/admin/page-shell";
import { PostForm } from "@/components/admin/post-form";

export default function EditPostPage({ params }: { params: { id: string } }) {
  return (
    <AdminPageShell title="编辑博客" description="支持草稿迭代和最终发布。">
      <PostForm postId={Number(params.id)} />
    </AdminPageShell>
  );
}
