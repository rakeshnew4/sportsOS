"use client";

import { use, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { cancelBooking, getMyBooking, openToCommunity } from "@/lib/api/bookings";
import { joinMatch, listParticipants } from "@/lib/api/matches";
import {
  confirmWaitlistPromotion,
  declineWaitlistPromotion,
  getMyWaitlistPosition,
  joinWaitlist,
  leaveWaitlist,
} from "@/lib/api/waitlist";
import { createRating } from "@/lib/api/ratings";
import { queryKeys } from "@/lib/queryKeys";
import { useSession } from "@/components/providers/SessionProvider";
import { Button } from "@/components/ui/Button";
import { ApiError } from "@/lib/api/client";
import type { BookingStatus } from "@/lib/types";

const STATUS_STYLES: Record<BookingStatus, string> = {
  confirmed: "bg-emerald-50 text-emerald-700",
  pending_payment: "bg-amber-50 text-amber-700",
  completed: "bg-neutral-100 text-neutral-600",
  cancelled: "bg-red-50 text-red-600",
};

export default function BookingDetailPage({ params }: { params: Promise<{ bookingId: string }> }) {
  const { bookingId } = use(params);
  const session = useSession();
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const [slotsOpen, setSlotsOpen] = useState("2");

  const { data: booking, isLoading } = useQuery({
    queryKey: [...queryKeys.myBookings(), bookingId],
    queryFn: () => getMyBooking(bookingId),
  });

  const tenantId = booking?.tenant_id;

  const { data: participants } = useQuery({
    queryKey: tenantId ? queryKeys.matchParticipants(tenantId, bookingId) : ["matchParticipants", "pending"],
    queryFn: () => listParticipants(tenantId!, bookingId),
    enabled: !!tenantId,
  });

  function invalidateBooking() {
    queryClient.invalidateQueries({ queryKey: queryKeys.myBookings() });
    if (tenantId) queryClient.invalidateQueries({ queryKey: queryKeys.matchParticipants(tenantId, bookingId) });
  }

  const cancelMutation = useMutation({
    mutationFn: () => cancelBooking(tenantId!, bookingId),
    onSuccess: () => {
      setError(null);
      invalidateBooking();
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not cancel booking"),
  });

  const openMutation = useMutation({
    mutationFn: () => openToCommunity(tenantId!, bookingId, Number(slotsOpen)),
    onSuccess: () => {
      setError(null);
      invalidateBooking();
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not open this match"),
  });

  const joinMutation = useMutation({
    mutationFn: () => joinMatch(tenantId!, bookingId),
    onSuccess: () => {
      setError(null);
      invalidateBooking();
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not join this match"),
  });

  const { data: waitlistPosition } = useQuery({
    queryKey: queryKeys.myWaitlistPosition(bookingId),
    queryFn: () => getMyWaitlistPosition(bookingId),
    enabled: !!booking && booking.is_joinable && booking.slots_open === 0,
    retry: false,
  });

  function invalidateWaitlist() {
    queryClient.invalidateQueries({ queryKey: queryKeys.myWaitlistPosition(bookingId) });
  }

  const joinWaitlistMutation = useMutation({
    mutationFn: () => joinWaitlist(tenantId!, bookingId),
    onSuccess: () => {
      setError(null);
      invalidateWaitlist();
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not join waitlist"),
  });

  const leaveWaitlistMutation = useMutation({
    mutationFn: () => leaveWaitlist(bookingId),
    onSuccess: () => {
      setError(null);
      invalidateWaitlist();
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not leave waitlist"),
  });

  const confirmWaitlistMutation = useMutation({
    mutationFn: () => confirmWaitlistPromotion(bookingId),
    onSuccess: () => {
      setError(null);
      invalidateWaitlist();
      invalidateBooking();
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not confirm your spot"),
  });

  const declineWaitlistMutation = useMutation({
    mutationFn: () => declineWaitlistPromotion(bookingId),
    onSuccess: () => {
      setError(null);
      invalidateWaitlist();
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not decline"),
  });

  const [ratedUids, setRatedUids] = useState<string[]>([]);

  if (isLoading) return <p className="text-sm text-neutral-500">Loading…</p>;
  if (!booking) return <p className="text-sm text-neutral-500">Booking not found.</p>;

  const isOwner = booking.created_by === session.uid;
  const canCancel = isOwner && (booking.status === "confirmed" || booking.status === "pending_payment");
  const canOpen = isOwner && booking.status === "confirmed";
  const canJoin = !isOwner && booking.is_joinable && booking.slots_open > 0 && booking.status === "confirmed";
  const isParticipant = isOwner || (participants?.some((p) => p.uid === session.uid) ?? false);
  const canWaitlist =
    !isOwner &&
    !isParticipant &&
    booking.is_joinable &&
    booking.slots_open === 0 &&
    booking.status === "confirmed";

  const otherPlayers = [booking.created_by, ...(participants?.map((p) => p.uid) ?? [])].filter(
    (uid) => uid !== session.uid && !ratedUids.includes(uid)
  );

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-bold">{booking.sport.replace("_", " ")}</h1>
          <p className="text-neutral-500 text-sm">
            {booking.date} · {booking.start_time} – {booking.end_time}
          </p>
          {booking.team_name && <p className="text-xs text-neutral-400 mt-1">{booking.team_name}</p>}
        </div>
        <span className={`text-xs font-medium rounded-full px-2 py-1 ${STATUS_STYLES[booking.status]}`}>
          {booking.status.replace("_", " ")}
        </span>
      </div>

      <p className="text-sm font-medium text-neutral-700">₹{booking.price}</p>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="rounded-2xl border border-neutral-200 bg-white p-4">
        <p className="text-sm font-semibold text-neutral-700 mb-2">
          Players ({participants?.length ?? 0})
        </p>
        <div className="space-y-1">
          {participants?.map((p) => (
            <p key={p.uid} className="text-sm text-neutral-600">
              {p.display_name || p.uid}
            </p>
          ))}
          {participants && participants.length === 0 && (
            <p className="text-sm text-neutral-400">No one has joined yet.</p>
          )}
        </div>
      </div>

      {canJoin && (
        <Button onClick={() => joinMutation.mutate()} disabled={joinMutation.isPending} className="w-full">
          {joinMutation.isPending ? "Joining…" : `Join this match (${booking.slots_open} open)`}
        </Button>
      )}

      {canWaitlist && !waitlistPosition && (
        <Button
          variant="secondary"
          onClick={() => joinWaitlistMutation.mutate()}
          disabled={joinWaitlistMutation.isPending}
          className="w-full"
        >
          {joinWaitlistMutation.isPending ? "Joining waitlist…" : "This match is full — join waitlist"}
        </Button>
      )}

      {waitlistPosition && (
        <div className="rounded-2xl border border-neutral-200 bg-white p-4 space-y-2">
          <p className="text-sm font-semibold text-neutral-700">
            Waitlist position #{waitlistPosition.position}
          </p>
          <p className="text-xs text-neutral-500 capitalize">Status: {waitlistPosition.status}</p>
          {waitlistPosition.status === "promoted" ? (
            <div className="flex gap-2">
              <Button
                onClick={() => confirmWaitlistMutation.mutate()}
                disabled={confirmWaitlistMutation.isPending}
              >
                Confirm spot
              </Button>
              <Button
                variant="secondary"
                onClick={() => declineWaitlistMutation.mutate()}
                disabled={declineWaitlistMutation.isPending}
              >
                Decline
              </Button>
            </div>
          ) : (
            <Button
              variant="ghost"
              onClick={() => leaveWaitlistMutation.mutate()}
              disabled={leaveWaitlistMutation.isPending}
              className="text-red-600"
            >
              Leave waitlist
            </Button>
          )}
        </div>
      )}

      {canOpen && !booking.is_joinable && (
        <div className="rounded-2xl border border-neutral-200 bg-white p-4 space-y-2">
          <p className="text-sm font-semibold text-neutral-700">Open to the community</p>
          <p className="text-xs text-neutral-500">
            Let other players join your slot and split the cost.
          </p>
          <div className="flex gap-2">
            <input
              type="number"
              min={1}
              value={slotsOpen}
              onChange={(e) => setSlotsOpen(e.target.value)}
              className="w-24 rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
            <Button
              variant="secondary"
              onClick={() => openMutation.mutate()}
              disabled={openMutation.isPending}
            >
              {openMutation.isPending ? "Opening…" : "Open slot"}
            </Button>
          </div>
        </div>
      )}

      {canCancel && (
        <Button
          variant="secondary"
          onClick={() => cancelMutation.mutate()}
          disabled={cancelMutation.isPending}
          className="w-full text-red-600"
        >
          {cancelMutation.isPending ? "Cancelling…" : "Cancel booking"}
        </Button>
      )}

      {booking.status === "completed" && otherPlayers.length > 0 && (
        <div className="rounded-2xl border border-neutral-200 bg-white p-4 space-y-3">
          <p className="text-sm font-semibold text-neutral-700">Rate your teammates</p>
          {otherPlayers.map((uid) => (
            <RatingForm
              key={uid}
              bookingId={bookingId}
              ratedUid={uid}
              onRated={() => setRatedUids((prev) => [...prev, uid])}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function RatingForm({
  bookingId,
  ratedUid,
  onRated,
}: {
  bookingId: string;
  ratedUid: string;
  onRated: () => void;
}) {
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () => createRating({ rated_uid: ratedUid, booking_id: bookingId, rating, comment }),
    onSuccess: () => onRated(),
    onError: (err) => setLocalError(err instanceof ApiError ? err.message : "Could not submit rating"),
  });

  return (
    <div className="space-y-1.5 border-t border-neutral-100 pt-3 first:border-t-0 first:pt-0">
      <p className="text-sm text-neutral-600 font-mono">{ratedUid.slice(0, 8)}…</p>
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((n) => (
          <button
            key={n}
            onClick={() => setRating(n)}
            className={`text-lg ${n <= rating ? "opacity-100" : "opacity-30"}`}
          >
            ⭐
          </button>
        ))}
      </div>
      <input
        placeholder="Comment (optional)"
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        className="w-full rounded-lg border border-neutral-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
      />
      {localError && <p className="text-xs text-red-600">{localError}</p>}
      <Button
        variant="secondary"
        onClick={() => mutation.mutate()}
        disabled={mutation.isPending}
        className="text-xs px-3 py-1.5"
      >
        {mutation.isPending ? "Submitting…" : "Submit rating"}
      </Button>
    </div>
  );
}
