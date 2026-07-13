"use client";

import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getCourt, listCourts } from "@/lib/api/venues";
import { getSlots, createBooking } from "@/lib/api/bookings";
import { suggestTeamNames } from "@/lib/api/teams";
import { useSlotsLive } from "@/lib/realtime/useSlotsLive";
import { queryKeys } from "@/lib/queryKeys";
import { toISODate } from "@/lib/date";
import { DateStrip } from "@/components/booking/DateStrip";
import { SlotGrid } from "@/components/booking/SlotGrid";
import { BookingSummary } from "@/components/booking/BookingSummary";
import { ApiError } from "@/lib/api/client";
import { FootballSpinner } from "@/components/ui/FootballSpinner";
import { Skeleton } from "@/components/ui/Skeleton";
import { getSportTheme, sportLabel } from "@/lib/sportTheme";
import { IndianRupee } from "lucide-react";
import { useSession } from "@/components/providers/SessionProvider";

const MIN_SLOT_LENGTH = 1; // 1 slot = 1 hour, enforced by 60-min granularity + the backend's 60-min minimum

export default function BookCourtPage({
  params,
}: {
  params: Promise<{ tenantId: string; courtId: string }>;
}) {
  const { tenantId, courtId } = use(params);
  const router = useRouter();
  const queryClient = useQueryClient();
  const session = useSession();

  const [date, setDate] = useState(() => {
    if (typeof window === "undefined") return toISODate(new Date());
    return new URLSearchParams(window.location.search).get("date") || toISODate(new Date());
  });
  const [selectedStart, setSelectedStart] = useState<number | null>(null);
  const [selectedLength, setSelectedLength] = useState(MIN_SLOT_LENGTH);
  const [error, setError] = useState<string | null>(null);
  const [teamName, setTeamName] = useState("");

  const { data: court } = useQuery({
    queryKey: ["court", tenantId, courtId],
    queryFn: () => getCourt(tenantId, courtId),
  });

  const { data: venueCourts } = useQuery({
    queryKey: queryKeys.courts(tenantId),
    queryFn: () => listCourts(tenantId),
  });
  const sameSportCourts = venueCourts?.filter((c) => c.sport === court?.sport) ?? [];

  const { data: nameSuggestions, refetch: refetchNames, isFetching: isFetchingNames } = useQuery({
    queryKey: ["teamNameSuggestions", court?.sport, session.display_name],
    queryFn: () => suggestTeamNames(court!.sport, session.display_name || "Captain"),
    enabled: !!court?.sport,
  });

  const { data: slots, isLoading } = useQuery({
    queryKey: queryKeys.slots(tenantId, courtId, date),
    queryFn: () => getSlots(tenantId, courtId, date),
  });

  useSlotsLive(tenantId, courtId, date);

  useEffect(() => {
    if (!teamName && nameSuggestions?.suggestions?.length) {
      setTeamName(nameSuggestions.suggestions[0]);
    }
  }, [nameSuggestions, teamName]);

  const bookMutation = useMutation({
    mutationFn: () => {
      if (!slots || selectedStart === null) throw new Error("No slot selected");
      const selected = slots.slice(selectedStart, selectedStart + selectedLength);
      return createBooking(tenantId, {
        court_id: courtId,
        date,
        start_time: selected[0].start_time,
        end_time: selected[selected.length - 1].end_time,
        team_name: teamName.trim() || undefined,
      });
    },
    onSuccess: (booking) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.slots(tenantId, courtId, date) });
      queryClient.invalidateQueries({ queryKey: queryKeys.myBookings() });
      router.push(`/bookings/${booking.booking_id}`);
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

  const theme = getSportTheme(court?.sport);
  const Icon = theme.icon;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <span className={`flex h-11 w-11 items-center justify-center rounded-xl ${theme.light}`}>
          <Icon size={20} strokeWidth={2.25} />
        </span>
        <div>
          {court ? <h1 className="text-xl font-bold">{court.name}</h1> : <Skeleton className="h-6 w-32" />}
          {court && (
            <p className="text-ink-muted text-sm flex items-center gap-1">
              {sportLabel(court.sport)} · <IndianRupee size={12} />
              {court.hourly_price}/hr
            </p>
          )}
        </div>
      </div>

      {sameSportCourts.length > 1 && (
        <div>
          <p className="text-xs font-semibold text-ink-muted uppercase tracking-wide mb-2">Court</p>
          <div className="flex gap-2 overflow-x-auto pb-1 -mx-1 px-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
            {sameSportCourts.map((c) => {
              const active = c.court_id === courtId;
              return (
                <button
                  key={c.court_id}
                  onClick={() => {
                    if (!active) router.push(`/venues/${tenantId}/courts/${c.court_id}/book?date=${date}`);
                  }}
                  className={`shrink-0 rounded-full px-4 py-2 text-xs font-semibold transition-colors ${
                    active
                      ? "bg-gradient-to-r from-brand-from to-brand-to text-white shadow-md shadow-indigo-600/20"
                      : "bg-surface-muted text-ink-muted hover:text-foreground"
                  }`}
                >
                  {c.name}
                </button>
              );
            })}
          </div>
        </div>
      )}

      <DateStrip selected={date} onSelect={handleSelectDate} />

      {isLoading && <FootballSpinner />}
      {slots && slots.length === 0 && (
        <p className="text-sm text-ink-muted">No slots available for this date.</p>
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
        teamName={teamName}
        onTeamNameChange={setTeamName}
        nameSuggestions={nameSuggestions?.suggestions ?? []}
        onShuffleNames={() => refetchNames()}
        isShufflingNames={isFetchingNames}
      />
    </div>
  );
}
