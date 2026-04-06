import { BlogCard } from "@/components/blog/blog-card";
import { SectionTitle } from "@/components/shared/section-title";
import { getPosts } from "@/lib/api";

export default async function BlogPage() {
  const posts = await getPosts({ page_size: 12 });

  return (
    <div className="space-y-8">
      <SectionTitle eyebrow="Journal" title="灵感日志" description="关于选购、佩戴、养护与情绪能量的长期记录。" />
      <div className="grid gap-6 md:grid-cols-3">
        {posts.items.map((post) => (
          <BlogCard key={post.id} post={post} />
        ))}
      </div>
    </div>
  );
}
