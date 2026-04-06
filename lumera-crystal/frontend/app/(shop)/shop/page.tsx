import { ShopConsole } from "@/components/shop/shop-console";
import { SectionTitle } from "@/components/shared/section-title";

export default function ShopPage() {
  return (
    <div className="space-y-8">
      <SectionTitle
        eyebrow="Shop"
        title="轻量商城控制台"
        description="基于当前系统快速搭建的商城闭环演示：库存、订单、支付、推荐、报表、积分优惠。"
      />
      <ShopConsole />
    </div>
  );
}
