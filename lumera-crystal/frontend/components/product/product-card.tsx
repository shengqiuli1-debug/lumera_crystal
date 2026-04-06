import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Product } from "@/types";

export function ProductCard({ product }: { product: Product }) {
  const isVideo = product.cover_image_asset?.media_kind === "video";

  return (
    <Link href={`/products/${product.slug}`}>
      <Card className="group overflow-hidden p-0">
        <div className="relative h-64 w-full overflow-hidden">
          {isVideo ? (
            <video src={product.cover_image} className="h-full w-full object-cover transition duration-500 group-hover:scale-105" muted loop playsInline />
          ) : (
            <img src={product.cover_image} alt={product.name} className="h-full w-full object-cover transition duration-500 group-hover:scale-105" />
          )}
        </div>
        <div className="space-y-2 p-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-ink/60">{product.crystal_type}</p>
            {product.is_new ? <Badge>NEW</Badge> : null}
          </div>
          <h3 className="font-medium text-ink">{product.name}</h3>
          <p className="line-clamp-2 text-sm text-ink/70">{product.short_description}</p>
          <p className="pt-2 text-sm font-medium text-ink">¥{product.price}</p>
        </div>
      </Card>
    </Link>
  );
}
