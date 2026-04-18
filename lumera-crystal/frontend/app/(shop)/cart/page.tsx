import { CartCheckout } from "@/components/shop/cart-checkout";
import { SectionTitle } from "@/components/shared/section-title";

export default function CartPage() {
  return (
    <div className="space-y-8">
      <SectionTitle
        eyebrow="Cart"
        title="购物车与下单"
        description="从购物车提交订单，并完成支付。"
      />
      <CartCheckout />
    </div>
  );
}
