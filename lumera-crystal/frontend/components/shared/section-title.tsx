import { ReactNode } from "react";

export function SectionTitle({ eyebrow, title, description, action }: { eyebrow: string; title: string; description?: string; action?: ReactNode }) {
  return (
    <div className="mb-8 flex items-end justify-between gap-4">
      <div>
        <p className="text-xs uppercase tracking-[0.2em] text-gold">{eyebrow}</p>
        <h2 className="mt-2 font-serif text-3xl text-ink md:text-4xl">{title}</h2>
        {description ? <p className="mt-3 max-w-2xl text-sm text-ink/70">{description}</p> : null}
      </div>
      {action}
    </div>
  );
}
