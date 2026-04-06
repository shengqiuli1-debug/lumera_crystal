import { ContactForm } from "@/components/forms/contact-form";
import { SectionTitle } from "@/components/shared/section-title";

export default function ContactPage() {
  return (
    <div className="grid gap-8 lg:grid-cols-[1fr_460px]">
      <div>
        <SectionTitle eyebrow="Contact" title="联系我们" description="合作咨询、选购建议、品牌联名，欢迎留下你的信息。" />
        <p className="text-sm leading-7 text-ink/75">
          我们通常会在 24 小时内回复。若你希望获得更精准推荐，请附上你的佩戴场景、偏好颜色和预算区间。
        </p>
      </div>
      <ContactForm />
    </div>
  );
}
