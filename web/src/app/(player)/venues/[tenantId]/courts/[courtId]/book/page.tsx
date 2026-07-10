"use client";

import { use, useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getCourt } from "@/lib/api/venues";
import { getSlots, createBooking } from "@/lib/api/bookings";
import { queryKeys } from "@/lib/queryKeys";
import { toISODate } from "@/lib/date";
import { DateStrip } from "@/components/booking/DateStrip";
import { SlotGrid } from "@/components/booking/SlotGrid";
import { BookingSummary } from "@/components/booking/BookingSummary";
import { ApiError } from "@/lib/api/client";

const MIN_SLOT_LENGTH = 2; // 2 x 30min = 1 hour minimum, enforced by the backend

export default function BookCourtPage({
  params,
}: {
  params: Promise<{ tenantId: string; courtId: string }>;
}) {
  const { tenantId, courtId } = use(params);
  const router = useRouter();
  const queryClient = useQueryClient();

  const [date, setDate] = useState(() => toISODate(new Date()));
  const [selectedStart, setSelectedStart] = useState<number | null>(null);
  const [selectedLength, setSelectedLength] = useState(MIN_SLOT_LENGTH);
  const [error, setError] = useState<string | null>(null);

  const { data: court } = useQuery({
    queryKey: ["court", tenantId, courtId],
    queryFn: () => getCourt(tenantId, courtId),
  });

  const { data: slots, isLoading } = useQuery({
    queryKey: queryKeys.slots(tenantId, courtId, date),
    queryFn: () => getSlots(tenantId, courtId, date),
  });

  const bookMutation = useMutation({
    mutationFn: () => {
      if (!slots || selectedStart === null) throw new Error("No slot selected");
      const selected = slots.slice(selectedStart, selectedStart + selectedLength);
      return createBooking(tenantId, {
        court_id: courtId,
        date,
        start_time: selected[0].start_time,
        end_time: selected[selected.length - 1].end_time,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.slots(tenantId, courtId, date) });
      queryClient.invalidateQueries({ queryKey: queryKeys.myBookings() });
      router.push("/bookings");
    },
    onError: (err) => {
      setError(err instanceof ApiError ? err.message : "Could not book that slot");
    },
  });

  function handleSelectDate(newDate: string) {
    setDate(newDate);
    setSelectedStart(null);
    setSelectedLength(MIN_SLOT_LENGTH);
    setError(null);
  }

  function handleSelectSlot(index: number) {
    if (!slots) return;
    // Need at least MIN_SLOT_LENGTH contiguous available slots starting here.
    for (let i = 0; i < MIN_SLOT_LENGTH; i++) {
      if (!slots[index + i] || !slots[index + i].available) return;
    }
    setSelectedStart(index);
    setSelectedLength(MIN_SLOT_LENGTH);
    setError(null);
  }

  const canExtend =
    !!slots &&
    selectedStart !== null &&
    !!slots[selectedStart + selectedLength] &&
    slots[selectedStart + selectedLength].available;

  const canShrink = selectedLength > MIN_SLOT_LENGTH;

  const selectedSlots =
    slots && selectedStart !== null ? slots.slice(selectedStart, selectedStart + selectedLength) : [];

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold">{court?.name || "Loading…"}</h1>
        <p className="text-neutral-500 text-sm">
          {court && `${court.sport.replace("_", " ")} · ₹${court.hourly_price}/hr`}
        </p>
      </div>

      <DateStrip selected={date} onSelect={handleSelectDate} />

      {isLoading && <p className="text-sm text-neutral-500">Loading slots…</p>}
      {slots && slots.length === 0 && (
        <p className="text-sm text-neutral-500">No slots available for this date.</p>
      )}
      {error && <p className="text-sm text-red-600">{error}</p>}

      {slots && (
        <SlotGrid
          slots={slots}
          selectedStart={selectedStart}
          selectedLength={selectedLength}
          onSelect={handleSelectSlot}
        />
      )}

      <BookingSummary
        date={date}
        selectedSlots={selectedSlots}
        canExtend={canExtend}
        canShrink={canShrink}
        onExtend={() => canExtend && setSelectedLength((l) => l + 1)}
        onShrink={() => canShrink && setSelectedLength((l) => l - 1)}
        onConfirm={() => bookMutation.mutate()}
        onClear={() => setSelectedStart(null)}
        loading={bookMutation.isPending}
      />
    </div>
  );
}
