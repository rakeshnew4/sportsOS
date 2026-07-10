"use client";

import { Button } from "@/components/ui/Button";
import type { SlotResponse } from "@/lib/types";

export function BookingSummary({
  date,
  selectedSlots,
  canExtend,
  canShrink,
  onExtend,
  onShrink,
  onConfirm,
  onClear,
  loading,
}: {
  date: string;
  selectedSlots: SlotResponse[];
  canExtend: boolean;
  canShrink: boolean;
  onExtend: () => void;
  onShrink: () => void;
  onConfirm: () => void;
  onClear: () => void;
  loading: boolean;
}) {
  if (selectedSlots.length === 0) return null;

  const startTime = selectedSlots[0].start_time;
  const endTime = selectedSlots[selectedSlots.length - 1].end_time;
  const totalPrice = selectedSlots.reduce((sum, s) => sum + (s.price ?? 0), 0);
  const durationHours = selectedSlots.length / 2;

  return (
    <div className="fixed bottom-16 md:bottom-0 left-0 right-0 z-20 border-t border-neutral-200 bg-white p-4 shadow-[0_-4px_12px_rgba(0,0,0,0.06)]">
      <div className="max-w-3xl mx-auto md:pl-56">
        <div className="flex items-center justify-between mb-3">
          <div>
            <p className="text-sm font-semibold text-neutral-900">
              {date} · {startTime} – {endTime}
            </p>
            <p className="text-xs text-neutral-500">
              {durationHours} hr{durationHours !== 1 ? "s" : ""} · ₹{totalPrice}
            </p>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={onShrink}
              disabled={!canShrink}
              className="h-8 w-8 rounded-full border border-neutral-300 text-neutral-600 disabled:opacity-30"
            >
              −
            </button>
            <span className="text-xs text-neutral-500 w-16 text-center">+30 min</span>
            <button
              onClick={onExtend}
              disabled={!canExtend}
              className="h-8 w-8 rounded-full border border-neutral-300 text-neutral-600 disabled:opacity-30"
            >
              +
            </button>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={onClear} className="flex-1">
            Clear
          </Button>
          <Button onClick={onConfirm} disabled={loading} className="flex-[2]">
            {loading ? "Booking…" : "Confirm & Book"}
          </Button>
        </div>
      </div>
    </div>
  );
}
