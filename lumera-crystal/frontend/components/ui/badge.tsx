import { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function Badge({ className, ...props }: HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border border-gold/40 bg-white/70 px-3 py-1 text-xs tracking-wide text-ink/80",
        className
      )}
      {...props}
    />
  );
}
