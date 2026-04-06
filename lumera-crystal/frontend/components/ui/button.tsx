import { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function Button({ className, ...props }: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center rounded-full border border-gold/70 bg-ink px-5 py-2.5 text-sm font-medium text-ivory transition hover:-translate-y-0.5 hover:shadow-soft disabled:opacity-50",
        className
      )}
      {...props}
    />
  );
}
