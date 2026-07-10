type BadgeVariant = "confirmed" | "pending" | "cancelled" | "completed" | "neutral" | "brand";

const VARIANT_CLASSES: Record<BadgeVariant, string> = {
  confirmed: "bg-emerald-50 text-emerald-700",
  pending: "bg-amber-50 text-amber-700",
  cancelled: "bg-red-50 text-red-600",
  completed: "bg-slate-100 text-slate-600",
  neutral: "bg-surface-muted text-ink-muted",
  brand: "bg-indigo-50 text-indigo-700",
};

const STATUS_TO_VARIANT: Record<string, BadgeVariant> = {
  confirmed: "confirmed",
  pending_payment: "pending",
  waiting: "pending",
  matched: "confirmed",
  cancelled: "cancelled",
  rejected: "cancelled",
  declined: "cancelled",
  completed: "completed",
};

export function Badge({
  children,
  variant,
  status,
  className = "",
}: {
  children: React.ReactNode;
  variant?: BadgeVariant;
  status?: string;
  className?: string;
}) {
  const resolved = variant ?? (status ? STATUS_TO_VARIANT[status] ?? "neutral" : "neutral");
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold capitalize ${VARIANT_CLASSES[resolved]} ${className}`}
    >
      {children}
    </span>
  );
}
