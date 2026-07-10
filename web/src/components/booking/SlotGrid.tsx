"use client";

import type { SlotResponse } from "@/lib/types";

function band(startTime: string): "Morning" | "Afternoon" | "Evening" {
  const hour = Number(startTime.split(":")[0]);
  if (hour < 12) return "Morning";
  if (hour < 18) return "Afternoon";
  return "Evening";
}

export function SlotGrid({
  slots,
  selectedStart,
  selectedLength,
  onSelect,
}: {
  slots: SlotResponse[];
  selectedStart: number | null;
  selectedLength: number;
  onSelect: (index: number) => void;
}) {
  const groups: Record<string, { slot: SlotResponse; index: number }[]> = {
    Morning: [],
    Afternoon: [],
    Evening: [],
  };
  slots.forEach((slot, index) => groups[band(slot.start_time)].push({ slot, index }));

  return (
    <div className="space-y-4">
      {(["Morning", "Afternoon", "Evening"] as const).map((label) =>
        groups[label].length > 0 ? (
          <div key={label}>
            <p className="text-xs font-semibold text-neutral-400 uppercase tracking-wide mb-2">{label}</p>
            <div className="grid grid-cols-4 gap-2">
              {groups[label].map(({ slot, index }) => {
                const isSelected =
                  selectedStart !== null && index >= selectedStart && index < selectedStart + selectedLength;
                return (
                  <button
                    key={slot.start_time}
                    disabled={!slot.available}
                    onClick={() => onSelect(index)}
                    className={`rounded-lg py-2 text-xs font-medium border transition-colors ${
                      !slot.available
                        ? "bg-neutral-100 text-neutral-300 border-neutral-100 cursor-not-allowed"
                        : isSelected
                          ? "bg-emerald-600 text-white border-emerald-600"
                          : "bg-white text-neutral-700 border-neutral-200 hover:border-emerald-400"
                    }`}
                  >
                    {slot.start_time}
                  </button>
                );
              })}
            </div>
          </div>
        ) : null
      )}
    </div>
  );
}
