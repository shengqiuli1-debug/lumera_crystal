import { ShopConsole } from "@/components/shop/shop-console";
import { SectionTitle } from "@/components/shared/section-title";

export default function ShopPage() {
  return (
    <div className="space-y-8">
      <SectionTitle
        eyebrow="Orders"
        title="订单中心"
        description="查看订单历史、待支付订单、已支付订单，并在这里完成支付。"
      />
      <ShopConsole />
    </div>
  );
}
