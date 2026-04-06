import { SectionTitle } from "@/components/shared/section-title";

export default function AboutPage() {
  return (
    <div className="space-y-8">
      <SectionTitle eyebrow="Brand" title="关于 LUMERA CRYSTAL" description="让天然晶石成为现代生活里可持续的温柔支持。" />
      <div className="rounded-3xl border border-mist/70 bg-white/80 p-8 text-sm leading-8 text-ink/80">
        <p>
          我们相信，真正的高级感来自克制、细节和长期陪伴。LUMERA CRYSTAL 以天然矿石为核心，
          结合现代设计语言和严谨工艺，打造可日常佩戴的轻奢饰品。
        </p>
        <p className="mt-4">
          在选材上，我们重视色泽稳定度、透度、纹理与触感；在设计上，我们避免“过度装饰”，
          让每件作品都能自然融入衣橱，同时保留能量与情绪表达。
        </p>
      </div>
    </div>
  );
}
