import { ALL_SPORTS, getSportTheme, sportLabel } from "@/lib/sportTheme";

export function SportFilterChips({
  value,
  onChange,
  sports = ALL_SPORTS,
  allowAll = true,
}: {
  value: string;
  onChange: (sport: string) => void;
  /** Scope the chip list (e.g. to a single venue's sports) instead of every sport in the app. */
  sports?: string[];
  /** Set false when the caller requires a single sport picked (e.g. creating a team) — hides "All". */
  allowAll?: boolean;
}) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-1 -mx-1 px-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
      {allowAll && (
        <button
          onClick={() => onChange("")}
          className={`shrink-0 rounded-full px-4 py-2 text-xs font-semibold transition-colors ${
            value === ""
              ? "bg-gradient-to-r from-brand-from to-brand-to text-white shadow-md shadow-indigo-600/20"
              : "bg-surface-muted text-ink-muted hover:text-foreground"
          }`}
        >
          All
        </button>
      )}
      {sports.map((sport) => {
        const theme = getSportTheme(sport);
        const Icon = theme.icon;
        const active = value === sport;
        return (
          <button
            key={sport}
            onClick={() => onChange(active ? "" : sport)}
            className={`shrink-0 flex items-center gap-1.5 rounded-full px-4 py-2 text-xs font-semibold capitalize transition-colors ${
              active
                ? "bg-gradient-to-r from-brand-from to-brand-to text-white shadow-md shadow-indigo-600/20"
                : "bg-surface-muted text-ink-muted hover:text-foreground"
            }`}
          >
            <Icon size={13} strokeWidth={2.5} />
            {sportLabel(sport)}
          </button>
        );
      })}
    </div>
  );
}
