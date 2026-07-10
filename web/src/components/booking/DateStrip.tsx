"use client";

import { nextNDays, formatDayLabel, toISODate } from "@/lib/date";

export function DateStrip({
  selected,
  onSelect,
}: {
  selected: string;
  onSelect: (date: string) => void;
}) {
  const days = nextNDays(7);

  return (
    <div className="flex gap-2 overflow-x-auto pb-1">
      {days.map((d) => {
        const iso = toISODate(d);
        const { weekday, day } = formatDayLabel(d);
        const isSelected = iso === selected;
        return (
          <button
            key={iso}
            onClick={() => onSelect(iso)}
            className={`flex flex-col items-center justify-center min-w-14 rounded-xl px-3 py-2 text-sm font-medium border transition-colors ${
              isSelected
                ? "bg-emerald-600 text-white border-emerald-600"
                : "bg-white text-neutral-700 border-neutral-200"
            }`}
          >
            <span className="text-xs opacity-80">{weekday}</span>
            <span className="text-base">{day}</span>
          </button>
        );
      })}
    </div>
  );
}
