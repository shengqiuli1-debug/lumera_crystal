"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import { addToCart, setCart, type CartItem } from "@/lib/cart";

type Props = {
  product: {
    id: number;
    slug: string;
    name: string;
    price: string;
    cover_image: string;
    stock: number;
  };
};

export function AddToCartPanel({ product }: Props) {
  const router = useRouter();
  const [quantity, setQuantity] = useState(1);
  const [message, setMessage] = useState("");

  const canBuy = useMemo(() => product.stock > 0, [product.stock]);

  function handleAdd() {
    if (!canBuy) {
      setMessage("当前商品暂时无库存，可先收藏后再来。");
      return;
    }
    const item: Omit<CartItem, "quantity"> = {
      product_id: product.id,
      slug: product.slug,
      name: product.name,
      price: product.price,
      cover_image: product.cover_image
    };
    addToCart(item, quantity);
    setMessage(`已加入购物车：${product.name} x ${quantity}`);
  }

  function handleBuyNow() {
    if (!canBuy) {
      setMessage("当前商品暂时无库存，可先收藏后再来。");
      return;
    }
    const item: CartItem = {
      product_id: product.id,
      slug: product.slug,
      name: product.name,
      price: product.price,
      cover_image: product.cover_image,
      quantity: Math.max(1, quantity)
    };
    setCart([item]);
    router.push("/cart");
  }

  return (
    <div className="space-y-3 rounded-2xl border border-mist/70 bg-gradient-to-br from-ivory/80 to-white p-4">
      <div className="flex items-center justify-between rounded-xl bg-ink/5 px-3 py-2">
        <p className="text-sm text-ink/75">库存状态</p>
        <p className="text-sm font-medium text-ink">{product.stock > 0 ? `${product.stock} 件` : "缺货"}</p>
      </div>
      <div className="flex items-center gap-2">
        <label htmlFor="detail-qty" className="text-sm text-ink/80">
          数量
        </label>
        <input
          id="detail-qty"
          className="w-20 rounded-lg border border-mist px-2 py-1 text-sm"
          type="number"
          min={1}
          max={Math.max(1, product.stock)}
          value={quantity}
          onChange={(e) => setQuantity(Math.max(1, Math.min(Number(e.target.value || 1), Math.max(1, product.stock))))}
          disabled={!canBuy}
        />
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={handleAdd}
          disabled={!canBuy}
          className="rounded-lg bg-ink px-4 py-2 text-sm text-ivory shadow-[0_10px_24px_-16px_rgba(34,34,34,0.9)] disabled:cursor-not-allowed disabled:opacity-50"
        >
          加入购物车
        </button>
        <button
          type="button"
          onClick={handleBuyNow}
          disabled={!canBuy}
          className="rounded-lg border border-ink px-4 py-2 text-sm text-ink disabled:cursor-not-allowed disabled:opacity-50"
        >
          立即购买
        </button>
        <Link href="/cart" className="rounded-lg border border-stone-300 px-4 py-2 text-sm text-ink">
          去下单
        </Link>
      </div>

      {message ? <p className="rounded-lg bg-ink/5 px-3 py-2 text-xs text-ink/75">{message}</p> : null}
    </div>
  );
}
