import { Card } from "@/components/ui/card";

const testimonials = [
  {
    name: "Miya",
    role: "品牌顾问",
    text: "不是一眼很喧闹的饰品，而是越戴越喜欢。它让我的日常节奏慢了下来。"
  },
  {
    name: "Iris",
    role: "创意从业者",
    text: "拉长石系列在光线变化里特别美，细节做得像高端成衣配饰。"
  },
  {
    name: "Yuna",
    role: "产品经理",
    text: "礼盒与文案非常克制高级，送礼体验比很多大牌更走心。"
  }
];

export function TestimonialSection() {
  return (
    <section className="grid gap-4 md:grid-cols-3">
      {testimonials.map((item) => (
        <Card key={item.name}>
          <p className="text-sm leading-7 text-ink/80">“{item.text}”</p>
          <p className="mt-4 text-sm font-medium">{item.name}</p>
          <p className="text-xs text-ink/60">{item.role}</p>
        </Card>
      ))}
    </section>
  );
}
