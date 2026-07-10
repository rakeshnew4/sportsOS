import { LucideIcon } from "lucide-react";
import { Button } from "./Button";

export function EmptyState({
  icon: Icon,
  title,
  description,
  actionLabel,
  onAction,
}: {
  icon: LucideIcon;
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
}) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-2xl border border-dashed border-border bg-surface-muted/50 px-6 py-10 text-center">
      <span className="flex h-11 w-11 items-center justify-center rounded-full bg-surface text-ink-muted shadow-sm">
        <Icon size={20} strokeWidth={2} />
      </span>
      <p className="text-sm font-semibold text-foreground">{title}</p>
      {description && <p className="text-xs text-ink-muted max-w-xs">{description}</p>}
      {actionLabel && onAction && (
        <Button variant="gradient" onClick={onAction} className="mt-2 text-xs px-4 py-2">
          {actionLabel}
        </Button>
      )}
    </div>
  );
}
