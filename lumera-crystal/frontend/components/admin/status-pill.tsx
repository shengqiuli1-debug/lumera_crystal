import { cn } from "@/lib/utils";

export function StatusPill({ status }: { status: string }) {
  return (
    <span
      className={cn(
        "rounded-full border px-2.5 py-1 text-xs",
        status === "active" || status === "published"
          ? "border-emerald-200 bg-emerald-50 text-emerald-700"
          : status === "draft"
            ? "border-amber-200 bg-amber-50 text-amber-700"
            : "border-stone-300 bg-stone-100 text-stone-600"
      )}
    >
      {status}
    </span>
  );
}
