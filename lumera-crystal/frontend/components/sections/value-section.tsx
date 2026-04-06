import { Card } from "@/components/ui/card";

const values = [
  { title: "天然来源", text: "严选产地可追溯矿石，尊重原始纹理与色泽。" },
  { title: "现代美学", text: "克制配色与轻奢细节，适配真实穿搭场景。" },
  { title: "情绪关怀", text: "以仪式感连接内在秩序，让佩戴成为日常修复。" }
];

export function ValueSection() {
  return (
    <section className="grid gap-4 md:grid-cols-3">
      {values.map((item) => (
        <Card key={item.title}>
          <h3 className="font-serif text-2xl">{item.title}</h3>
          <p className="mt-3 text-sm leading-7 text-ink/70">{item.text}</p>
        </Card>
      ))}
    </section>
  );
}
