import Link from "next/link";

import { BlogCard } from "@/components/blog/blog-card";
import { ProductGrid } from "@/components/product/product-grid";
import { HeroSection } from "@/components/sections/hero-section";
import { NewsletterSection } from "@/components/sections/newsletter-section";
import { TestimonialSection } from "@/components/sections/testimonial-section";
import { ValueSection } from "@/components/sections/value-section";
import { SectionTitle } from "@/components/shared/section-title";
import { getCategories, getPosts, getProducts } from "@/lib/api";

export default async function HomePage() {
  const [categories, productsResp, postsResp] = await Promise.all([
    getCategories(),
    getProducts({ page_size: 6 }),
    getPosts({ page_size: 3 })
  ]);

  return (
    <div className="space-y-16">
      <HeroSection />
      <ValueSection />

      <section>
        <SectionTitle eyebrow="Categories" title="热门分类" description="按能量与风格筛选你当下需要的晶石。" />
        <div className="grid gap-4 md:grid-cols-4">
          {categories.slice(0, 8).map((category) => (
            <Link
              key={category.id}
              href={"/categories/" + category.slug}
              className="rounded-2xl border border-mist/70 bg-white/80 p-4 text-sm hover:border-gold"
            >
              <p className="font-medium">{category.name}</p>
              <p className="mt-2 text-xs text-ink/60">{category.description}</p>
            </Link>
          ))}
        </div>
      </section>

      <section>
        <SectionTitle
          eyebrow="Featured"
          title="精选商品"
          description="轻奢质感与佩戴舒适度并重，适合长期陪伴。"
          action={
            <Link href="/products" className="text-sm text-ink/70 hover:text-ink">
              查看全部 →
            </Link>
          }
        />
        <ProductGrid products={productsResp.items} />
      </section>

      <section className="rounded-3xl border border-mist/70 bg-white/70 p-8">
        <SectionTitle eyebrow="Intentions" title="场景与寓意" description="为不同阶段的自己，选择更贴合的能量关键词。" />
        <div className="grid gap-3 text-sm md:grid-cols-5">
          {["爱情", "疗愈", "守护", "财富", "平静"].map((item) => (
            <div key={item} className="rounded-2xl border border-mist bg-ivory px-4 py-3 text-center">
              {item}
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-3xl border border-mist/70 bg-white/70 p-8">
        <SectionTitle eyebrow="Story" title="品牌故事" />
        <p className="max-w-3xl text-sm leading-8 text-ink/75">
          LUMERA CRYSTAL 创立于对“慢一点也没关系”的生活信念。我们希望通过天然矿石的纹理与光泽，
          把一种温柔的秩序感带回日常。每件作品都强调可穿戴、可陪伴、可沉淀，让美感与情绪支持同频出现。
        </p>
      </section>

      <section>
        <SectionTitle eyebrow="Testimonials" title="用户评价" />
        <TestimonialSection />
      </section>

      <section>
        <SectionTitle eyebrow="Journal" title="灵感日志" />
        <div className="grid gap-6 md:grid-cols-3">
          {postsResp.items.map((post) => (
            <BlogCard key={post.id} post={post} />
          ))}
        </div>
      </section>

      <NewsletterSection />
    </div>
  );
}
