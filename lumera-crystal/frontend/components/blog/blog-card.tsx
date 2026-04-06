import Link from "next/link";

import { Card } from "@/components/ui/card";
import { Post } from "@/types";

export function BlogCard({ post }: { post: Post }) {
  return (
    <Link href={`/blog/${post.slug}`}>
      <Card className="group overflow-hidden p-0">
        <div className="relative h-56 w-full overflow-hidden">
          <img src={post.cover_image} alt={post.title} className="h-full w-full object-cover transition duration-500 group-hover:scale-105" />
        </div>
        <div className="space-y-2 p-4">
          <h3 className="font-medium">{post.title}</h3>
          <p className="line-clamp-2 text-sm text-ink/70">{post.excerpt}</p>
          <p className="text-xs uppercase tracking-wide text-gold">{post.author}</p>
        </div>
      </Card>
    </Link>
  );
}
