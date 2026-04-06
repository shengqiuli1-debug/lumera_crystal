import Image from "next/image";
import Link from "next/link";

import { SectionTitle } from "@/components/shared/section-title";
import { getCategories } from "@/lib/api";

export default async function CategoriesPage() {
  const categories = await getCategories();

  return (
    <div className="space-y-8">
      <SectionTitle eyebrow="Categories" title="晶石分类" description="按矿石类型探索 LUMERA 的完整系列。" />
      <div className="grid gap-6 md:grid-cols-3">
        {categories.map((category) => (
          <Link key={category.id} href={"/categories/" + category.slug} className="group overflow-hidden rounded-3xl border border-mist/70 bg-white/80">
            <div className="relative h-56 w-full overflow-hidden">
              <Image src={category.cover_image} alt={category.name} fill className="object-cover transition duration-500 group-hover:scale-105" />
            </div>
            <div className="p-5">
              <p className="font-medium">{category.name}</p>
              <p className="mt-2 text-sm text-ink/70">{category.description}</p>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
