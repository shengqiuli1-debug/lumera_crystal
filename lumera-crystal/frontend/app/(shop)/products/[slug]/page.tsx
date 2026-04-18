import { Badge } from "@/components/ui/badge";
import { ProductMediaGallery } from "@/components/product/product-media-gallery";
import { AddToCartPanel } from "@/components/shop/add-to-cart-panel";
import { getProduct } from "@/lib/api";

export default async function ProductDetailPage({ params }: { params: { slug: string } }) {
  const product = await getProduct(params.slug);

  return (
    <div className="grid gap-8 xl:grid-cols-[1.15fr_0.85fr]">
      <section className="rounded-3xl border border-mist/70 bg-white/90 p-4 shadow-[0_16px_36px_-28px_rgba(34,32,28,0.75)]">
        <ProductMediaGallery
          name={product.name}
          coverImage={product.cover_image}
          coverAsset={product.cover_image_asset}
          galleryImages={product.gallery_images}
          galleryAssets={product.gallery_image_assets}
        />
      </section>

      <section className="space-y-5 xl:sticky xl:top-24 xl:h-fit">
        <div className="space-y-4 rounded-3xl border border-ink/10 bg-gradient-to-br from-ink to-stone-800 p-6 text-ivory shadow-[0_18px_40px_-24px_rgba(20,20,20,0.9)]">
          <div className="flex flex-wrap items-center gap-2">
            <Badge>{product.intention}</Badge>
            {product.is_new ? <Badge>NEW</Badge> : null}
            <Badge>{product.status === "active" ? "在售" : "暂不可售"}</Badge>
          </div>
          <h1 className="font-serif text-4xl leading-tight">{product.name}</h1>
          <p className="text-sm text-ivory/75">{product.subtitle}</p>
          <div className="flex items-end justify-between gap-3">
            <p className="text-3xl font-semibold">¥{product.price}</p>
            <p className="rounded-full border border-ivory/20 px-2.5 py-1 text-xs text-ivory/80">
              库存 {product.stock}
            </p>
          </div>
        </div>

        <div className="rounded-3xl border border-mist/70 bg-white/90 p-5 shadow-[0_14px_32px_-26px_rgba(34,32,28,0.8)]">
          <h2 className="mb-3 text-base font-semibold text-ink">购买操作</h2>
          <AddToCartPanel
            product={{
              id: product.id,
              slug: product.slug,
              name: product.name,
              price: product.price,
              cover_image: product.cover_image,
              stock: product.stock
            }}
          />
        </div>

        <div className="rounded-3xl border border-mist/70 bg-white/90 p-5 shadow-[0_14px_32px_-26px_rgba(34,32,28,0.8)]">
          <h2 className="mb-3 text-base font-semibold text-ink">晶石说明</h2>
          <p className="text-sm leading-7 text-ink/80">{product.full_description}</p>
        </div>

        <div className="grid grid-cols-2 gap-3 rounded-3xl border border-mist/70 bg-white/90 p-5 text-sm text-ink/75 shadow-[0_14px_32px_-26px_rgba(34,32,28,0.8)]">
          <p className="rounded-xl bg-ivory/70 px-3 py-2">颜色：{product.color}</p>
          <p className="rounded-xl bg-ivory/70 px-3 py-2">产地：{product.origin}</p>
          <p className="rounded-xl bg-ivory/70 px-3 py-2">尺寸：{product.size}</p>
          <p className="rounded-xl bg-ivory/70 px-3 py-2">材质：{product.material}</p>
          <p className="rounded-xl bg-ivory/70 px-3 py-2">脉轮：{product.chakra}</p>
          <p className="rounded-xl bg-ivory/70 px-3 py-2">晶石类型：{product.crystal_type}</p>
        </div>

        <div className="rounded-3xl border border-mist/70 bg-white/90 p-5 text-sm text-ink/80 shadow-[0_14px_32px_-26px_rgba(34,32,28,0.8)]">
          <h2 className="mb-2 text-base font-semibold text-ink">服务承诺</h2>
          <p>下单后进入支付流程，支付成功后自动触发库存扣减与发货请求。若库存变动导致下单失败，系统会给出明确提示。</p>
        </div>
      </section>
    </div>
  );
}
