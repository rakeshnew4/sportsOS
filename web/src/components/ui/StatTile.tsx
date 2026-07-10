import { LucideIcon } from "lucide-react";

export function StatTile({
  icon: Icon,
  label,
  value,
  accent = "text-indigo-600 bg-indigo-50",
}: {
  icon: LucideIcon;
  label: string;
  value: string | number;
  accent?: string;
}) {
  return (
    <div className="flex flex-col items-center gap-1.5 text-center">
      <span className={`flex h-9 w-9 items-center justify-center rounded-full ${accent}`}>
        <Icon size={16} strokeWidth={2.25} />
      </span>
      <p className="text-lg font-bold tabular-nums leading-none">{value}</p>
      <p className="text-xs text-ink-muted leading-none">{label}</p>
    </div>
  );
}
