"use client";

import { use, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { checkinPlayer, completeMatch, listVenueBookings } from "@/lib/api/bookings";
import { listParticipants } from "@/lib/api/matches";
import { queryKeys } from "@/lib/queryKeys";
import { toISODate } from "@/lib/date";
import { Button } from "@/components/ui/Button";
import { ApiError } from "@/lib/api/client";
import type { BookingResponse } from "@/lib/types";

export default function VenueBookingsPage({ params }: { params: Promise<{ tenantId: string }> }) {
  const { tenantId } = use(params);
  const [date, setDate] = useState(() => toISODate(new Date()));

  const { data: bookings, isLoading } = useQuery({
    queryKey: queryKeys.venueBookings(tenantId, date),
    queryFn: () => listVenueBookings(tenantId, date),
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Bookings</h1>
        <input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          className="rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
        />
      </div>

      {isLoading && <p className="text-sm text-neutral-500">Loading…</p>}
      {bookings && bookings.length === 0 && (
        <p className="text-sm text-neutral-500">No bookings on this date.</p>
      )}

      <div className="space-y-3">
        {bookings?.map((booking) => (
          <BookingRow key={booking.booking_id} tenantId={tenantId} booking={booking} />
        ))}
      </div>
    </div>
  );
}

function BookingRow({ tenantId, booking }: { tenantId: string; booking: BookingResponse }) {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<string | null>(null);

  const { data: participants } = useQuery({
    queryKey: queryKeys.matchParticipants(tenantId, booking.booking_id),
    queryFn: () => listParticipants(tenantId, booking.booking_id),
    enabled: booking.status === "confirmed",
  });

  const checkinMutation = useMutation({
    mutationFn: (playerUid: string) => checkinPlayer(tenantId, booking.booking_id, playerUid),
    onSuccess: () => setError(null),
    onError: (err) => setError(err instanceof ApiError ? err.message : "Check-in failed"),
  });

  const completeMutation = useMutation({
    mutationFn: () => completeMatch(tenantId, booking.booking_id),
    onSuccess: (res) => {
      setError(null);
      setResult(res.message);
      queryClient.invalidateQueries({ queryKey: ["venueBookings"] });
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not complete match"),
  });

  const attendees = [booking.created_by, ...(participants?.map((p) => p.uid) ?? [])];

  return (
    <div className="rounded-2xl border border-neutral-200 bg-white p-4 space-y-2">
      <div className="flex items-start justify-between">
        <div>
          <p className="font-semibold text-neutral-900">{booking.sport.replace("_", " ")}</p>
          <p className="text-sm text-neutral-500">
            {booking.start_time} – {booking.end_time}
          </p>
        </div>
        <span className="text-xs font-medium rounded-full px-2 py-1 bg-neutral-100 text-neutral-600">
          {booking.status.replace("_", " ")}
        </span>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}
      {result && <p className="text-sm text-emerald-600">{result}</p>}

      {booking.status === "confirmed" && (
        <div className="flex flex-wrap gap-2">
          {attendees.map((uid) => (
            <Button
              key={uid}
              variant="secondary"
              onClick={() => checkinMutation.mutate(uid)}
              disabled={checkinMutation.isPending}
              className="text-xs px-2 py-1"
            >
              Check in {uid.slice(0, 8)}…
            </Button>
          ))}
          <Button
            onClick={() => completeMutation.mutate()}
            disabled={completeMutation.isPending}
            className="text-xs px-2 py-1"
          >
            {completeMutation.isPending ? "Completing…" : "Complete match"}
          </Button>
        </div>
      )}
    </div>
  );
}
