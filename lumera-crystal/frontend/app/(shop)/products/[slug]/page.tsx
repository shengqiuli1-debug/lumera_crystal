import { Badge } from "@/components/ui/badge";
import { ProductMediaGallery } from "@/components/product/product-media-gallery";
import { getProduct } from "@/lib/api";

export default async function ProductDetailPage({ params }: { params: { slug: string } }) {
  const product = await getProduct(params.slug);

  return (
    <div className="grid gap-8 lg:grid-cols-2">
      <ProductMediaGallery
        name={product.name}
        coverImage={product.cover_image}
        coverAsset={product.cover_image_asset}
        galleryImages={product.gallery_images}
        galleryAssets={product.gallery_image_assets}
      />

      <div className="space-y-5 rounded-3xl border border-mist/70 bg-white/80 p-6">
        <div className="flex items-center gap-2">
          <Badge>{product.intention}</Badge>
          {product.is_new ? <Badge>NEW</Badge> : null}
        </div>
        <h1 className="font-serif text-4xl">{product.name}</h1>
        <p className="text-sm text-ink/70">{product.subtitle}</p>
        <p className="text-2xl font-medium">¥{product.price}</p>
        <p className="text-sm leading-7 text-ink/80">{product.full_description}</p>

        <div className="grid grid-cols-2 gap-3 text-sm text-ink/75">
          <p>颜色：{product.color}</p>
          <p>产地：{product.origin}</p>
          <p>尺寸：{product.size}</p>
          <p>材质：{product.material}</p>
          <p>脉轮：{product.chakra}</p>
          <p>库存：{product.stock}</p>
        </div>
      </div>
    </div>
  );
}
