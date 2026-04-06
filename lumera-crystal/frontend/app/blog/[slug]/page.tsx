import { Badge } from "@/components/ui/badge";
import { getPost } from "@/lib/api";

export default async function BlogDetailPage({ params }: { params: { slug: string } }) {
  const post = await getPost(params.slug);

  return (
    <article className="mx-auto max-w-4xl space-y-8">
      <div className="space-y-3">
        <div className="flex gap-2">
          {post.tags.map((tag) => (
            <Badge key={tag}>{tag}</Badge>
          ))}
        </div>
        <h1 className="font-serif text-4xl">{post.title}</h1>
        <p className="text-sm text-ink/70">{post.excerpt}</p>
      </div>
      <div className="relative h-[420px] overflow-hidden rounded-3xl border border-mist/70">
        <img src={post.cover_image} alt={post.title} className="h-full w-full object-cover" />
      </div>
      <div className="prose-content" dangerouslySetInnerHTML={{ __html: post.content.replace(/\n/g, "<br />") }} />
    </article>
  );
}
