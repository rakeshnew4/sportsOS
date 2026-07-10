"use client";

import { Minus, Plus, Shuffle } from "lucide-react";
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
  teamName,
  onTeamNameChange,
  nameSuggestions = [],
  onShuffleNames,
  isShufflingNames,
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
  teamName?: string;
  onTeamNameChange?: (value: string) => void;
  nameSuggestions?: string[];
  onShuffleNames?: () => void;
  isShufflingNames?: boolean;
}) {
  if (selectedSlots.length === 0) return null;

  const startTime = selectedSlots[0].start_time;
  const endTime = selectedSlots[selectedSlots.length - 1].end_time;
  const totalPrice = selectedSlots.reduce((sum, s) => sum + (s.price ?? 0), 0);
  const durationHours = selectedSlots.length / 2;

  return (
    <div className="fixed bottom-16 md:bottom-0 left-0 right-0 z-20 border-t border-border bg-surface p-4 shadow-[0_-8px_24px_rgba(0,0,0,0.08)] rounded-t-3xl md:rounded-none">
      <div className="max-w-3xl mx-auto md:pl-56">
        <div className="flex items-center justify-between mb-3">
          <div>
            <p className="text-sm font-semibold">
              {date} · {startTime} – {endTime}
            </p>
            <p className="text-xs text-ink-muted">
              {durationHours} hr{durationHours !== 1 ? "s" : ""} · ₹{totalPrice}
            </p>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={onShrink}
              disabled={!canShrink}
              className="flex h-8 w-8 items-center justify-center rounded-full border border-border text-ink-muted disabled:opacity-30"
            >
              <Minus size={14} />
            </button>
            <span className="text-xs text-ink-muted w-16 text-center">+30 min</span>
            <button
              onClick={onExtend}
              disabled={!canExtend}
              className="flex h-8 w-8 items-center justify-center rounded-full border border-border text-ink-muted disabled:opacity-30"
            >
              <Plus size={14} />
            </button>
          </div>
        </div>

        {onTeamNameChange && (
          <div className="mb-3 space-y-1.5">
            <div className="flex items-center gap-2">
              <input
                value={teamName ?? ""}
                onChange={(e) => onTeamNameChange(e.target.value)}
                placeholder="Team name"
                maxLength={60}
                className="flex-1 rounded-xl border border-border bg-surface px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              {onShuffleNames && (
                <button
                  type="button"
                  onClick={onShuffleNames}
                  disabled={isShufflingNames}
                  title="Suggest another name"
                  className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-border text-ink-muted disabled:opacity-40"
                >
                  <Shuffle size={14} className={isShufflingNames ? "animate-spin" : ""} />
                </button>
              )}
            </div>
            {nameSuggestions.length > 1 && (
              <div className="flex flex-wrap gap-1.5">
                {nameSuggestions
                  .filter((name) => name !== teamName)
                  .map((name) => (
                    <button
                      key={name}
                      type="button"
                      onClick={() => onTeamNameChange(name)}
                      className="rounded-full border border-border bg-surface-muted px-2.5 py-1 text-xs text-ink-muted hover:text-foreground"
                    >
                      {name}
                    </button>
                  ))}
              </div>
            )}
          </div>
        )}

        <div className="flex gap-2">
          <Button variant="secondary" onClick={onClear} className="flex-1">
            Clear
          </Button>
          <Button variant="gradient" onClick={onConfirm} disabled={loading} className="flex-[2]">
            {loading ? "Booking…" : "Confirm & Book"}
          </Button>
        </div>
      </div>
    </div>
  );
}
