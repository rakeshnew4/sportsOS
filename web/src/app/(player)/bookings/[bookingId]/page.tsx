"use client";

import { use, useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { MessageCircle, Star, UserPlus, Users2, Wallet } from "lucide-react";
import { cancelBooking, getMyBooking, openToCommunity } from "@/lib/api/bookings";
import { getVenue } from "@/lib/api/venues";
import { joinMatch, listParticipants } from "@/lib/api/matches";
import {
  confirmWaitlistPromotion,
  declineWaitlistPromotion,
  getMyWaitlistPosition,
  joinWaitlist,
  leaveWaitlist,
} from "@/lib/api/waitlist";
import { createRating } from "@/lib/api/ratings";
import { getInviteCandidates, sendInvites } from "@/lib/api/invites";
import { queryKeys } from "@/lib/queryKeys";
import { useSession } from "@/components/providers/SessionProvider";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { FootballSpinner } from "@/components/ui/FootballSpinner";
import { ApiError } from "@/lib/api/client";
import { getSportTheme, sportLabel } from "@/lib/sportTheme";
import { toISODate } from "@/lib/date";

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

  const { data: venue } = useQuery({
    queryKey: tenantId ? queryKeys.venue(tenantId) : ["venue", "pending"],
    queryFn: () => getVenue(tenantId!),
    enabled: !!tenantId,
  });

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

  const [inviteOpen, setInviteOpen] = useState(false);
  const [selectedInvites, setSelectedInvites] = useState<Record<string, string>>({}); // uid -> tier
  const [invitesSent, setInvitesSent] = useState(false);

  const { data: inviteCandidates, isLoading: candidatesLoading } = useQuery({
    queryKey: tenantId ? queryKeys.inviteCandidates(tenantId, bookingId) : ["inviteCandidates", "pending"],
    queryFn: () => getInviteCandidates(tenantId!, bookingId),
    enabled: !!tenantId && inviteOpen,
  });

  const sendInvitesMutation = useMutation({
    mutationFn: () =>
      sendInvites(
        tenantId!,
        bookingId,
        Object.entries(selectedInvites).map(([to_uid, tier]) => ({ to_uid, tier }))
      ),
    onSuccess: () => {
      setError(null);
      setInvitesSent(true);
      setSelectedInvites({});
      queryClient.invalidateQueries({ queryKey: queryKeys.inviteCandidates(tenantId!, bookingId) });
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not send invites"),
  });

  function toggleInvite(uid: string, tier: string) {
    setSelectedInvites((prev) => {
      const next = { ...prev };
      if (next[uid]) delete next[uid];
      else next[uid] = tier;
      return next;
    });
  }

  if (isLoading) return <FootballSpinner />;
  if (!booking) return <p className="text-sm text-ink-muted">Booking not found.</p>;

  const theme = getSportTheme(booking.sport);
  const Icon = theme.icon;

  const isOwner = booking.created_by === session.uid;
  const canCancel = isOwner && (booking.status === "confirmed" || booking.status === "pending_payment");
  const canOpen = isOwner && booking.status === "confirmed";
  const canInvite = isOwner && booking.status === "confirmed" && booking.date >= toISODate(new Date());
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
        <div className="flex items-center gap-3">
          <span className={`flex h-11 w-11 items-center justify-center rounded-xl ${theme.light}`}>
            <Icon size={20} strokeWidth={2.25} />
          </span>
          <div>
            <h1 className="text-xl font-bold">{sportLabel(booking.sport)}</h1>
            <p className="text-ink-muted text-sm">
              {booking.date} · {booking.start_time} – {booking.end_time}
            </p>
            <p className="text-xs text-ink-muted mt-0.5">
              {booking.team_name && <span>{booking.team_name} · </span>}
              Hosted by{" "}
              <Link href={`/players/${booking.created_by}`} className="font-medium text-foreground hover:underline">
                {booking.created_by_name || "player"}
              </Link>
            </p>
          </div>
        </div>
        <Badge status={booking.status}>{booking.status.replace("_", " ")}</Badge>
      </div>

      <p className="text-sm font-semibold">₹{booking.price}</p>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {isOwner && booking.status === "pending_payment" && venue && (
        <Card className="space-y-3">
          <p className="text-sm font-semibold flex items-center gap-1.5">
            <Wallet size={15} /> Pay the venue directly
          </p>
          <p className="text-xs text-ink-muted">
            The venue confirms your booking here once they&apos;ve received payment.
          </p>
          <div className="space-y-2">
            {venue.upi_id ? (
              <a
                href={`upi://pay?pa=${encodeURIComponent(venue.upi_id)}&pn=${encodeURIComponent(
                  venue.name
                )}&am=${booking.price}&cu=INR&tn=${encodeURIComponent(`${sportLabel(booking.sport)} booking`)}`}
                className="block"
              >
                <Button variant="gradient" pill className="w-full">
                  Pay ₹{booking.price} via UPI
                </Button>
              </a>
            ) : (
              <p className="text-xs text-amber-700 bg-amber-50 rounded-lg px-3 py-2">
                This venue hasn&apos;t added a UPI ID yet — use the phone number below to arrange payment.
              </p>
            )}
            {venue.booking_phone && (
              <a
                href={`https://wa.me/${normalizePhone(venue.booking_phone)}?text=${encodeURIComponent(
                  `Hi, I booked ${sportLabel(booking.sport)} on ${booking.date} at ${booking.start_time}–${booking.end_time} (₹${booking.price}). Confirming my booking here.`
                )}`}
                target="_blank"
                rel="noopener noreferrer"
                className="block"
              >
                <Button variant="secondary" pill className="w-full flex items-center justify-center gap-1.5">
                  <MessageCircle size={15} /> Chat on WhatsApp
                </Button>
              </a>
            )}
          </div>
        </Card>
      )}

      <Card>
        <p className="text-sm font-semibold mb-2 flex items-center gap-1.5">
          <Users2 size={15} /> Players ({participants?.length ?? 0})
        </p>
        <div className="space-y-1">
          {participants?.map((p) => (
            <Link
              key={p.uid}
              href={`/players/${p.uid}`}
              className="block text-sm text-ink-muted hover:text-foreground hover:underline"
            >
              {p.display_name || p.uid}
            </Link>
          ))}
          {participants && participants.length === 0 && (
            <p className="text-sm text-ink-muted/70">No one has joined yet.</p>
          )}
        </div>
      </Card>

      {canInvite && (
        <Card className="space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold flex items-center gap-1.5">
              <UserPlus size={15} /> Invite players
            </p>
            {!inviteOpen && (
              <Button variant="secondary" onClick={() => setInviteOpen(true)} className="text-xs px-3 py-1.5">
                Find players
              </Button>
            )}
          </div>

          {inviteOpen && (
            <>
              {candidatesLoading && <p className="text-xs text-ink-muted">Finding players…</p>}
              {invitesSent && (
                <p className="text-xs text-emerald-600">Invites sent! They&apos;ll show up in the players&apos; notifications.</p>
              )}
              {inviteCandidates && inviteCandidates.length === 0 && (
                <p className="text-xs text-ink-muted/70">
                  No one to suggest right now — no past playmates, no one queued for this slot, and no
                  nearby players opted in to invites.
                </p>
              )}
              {inviteCandidates && inviteCandidates.length > 0 && (
                <>
                  {(["playmate", "queue", "nearby"] as const).map((tier) => {
                    const inTier = inviteCandidates.filter((c) => c.tier === tier);
                    if (inTier.length === 0) return null;
                    const tierLabel =
                      tier === "playmate"
                        ? "Played with before"
                        : tier === "queue"
                        ? "Looking for a game right now"
                        : "Nearby, open to invites";
                    return (
                      <div key={tier} className="space-y-1.5">
                        <p className="text-xs font-semibold text-ink-muted uppercase tracking-wide">{tierLabel}</p>
                        {inTier.map((c) => (
                          <label
                            key={c.uid}
                            className="flex items-center gap-2 rounded-xl border border-border px-3 py-2 text-sm"
                          >
                            <input
                              type="checkbox"
                              checked={!!selectedInvites[c.uid]}
                              onChange={() => toggleInvite(c.uid, c.tier)}
                            />
                            <span className="flex-1">{c.display_name}</span>
                            <span className="text-xs text-ink-muted">{c.reason}</span>
                          </label>
                        ))}
                      </div>
                    );
                  })}
                  <Button
                    variant="gradient"
                    onClick={() => sendInvitesMutation.mutate()}
                    disabled={Object.keys(selectedInvites).length === 0 || sendInvitesMutation.isPending}
                    className="w-full"
                  >
                    {sendInvitesMutation.isPending
                      ? "Sending…"
                      : `Send invite${Object.keys(selectedInvites).length === 1 ? "" : "s"}${
                          Object.keys(selectedInvites).length ? ` (${Object.keys(selectedInvites).length})` : ""
                        }`}
                  </Button>
                </>
              )}
            </>
          )}
        </Card>
      )}

      {canJoin && (
        <Button variant="gradient" pill onClick={() => joinMutation.mutate()} disabled={joinMutation.isPending} className="w-full">
          {joinMutation.isPending ? "Joining…" : `Join this match (${booking.slots_open} open)`}
        </Button>
      )}

      {canWaitlist && !waitlistPosition && (
        <Button
          variant="secondary"
          pill
          onClick={() => joinWaitlistMutation.mutate()}
          disabled={joinWaitlistMutation.isPending}
          className="w-full"
        >
          {joinWaitlistMutation.isPending ? "Joining waitlist…" : "This match is full — join waitlist"}
        </Button>
      )}

      {waitlistPosition && (
        <Card className="space-y-2">
          <p className="text-sm font-semibold">Waitlist position #{waitlistPosition.position}</p>
          <p className="text-xs text-ink-muted capitalize">Status: {waitlistPosition.status}</p>
          {waitlistPosition.status === "promoted" ? (
            <div className="flex gap-2">
              <Button
                variant="gradient"
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
        </Card>
      )}

      {canOpen && !booking.is_joinable && (
        <Card className="space-y-2">
          <p className="text-sm font-semibold">Open to the community</p>
          <p className="text-xs text-ink-muted">Let other players join your slot and split the cost.</p>
          <div className="flex gap-2">
            <input
              type="number"
              min={1}
              value={slotsOpen}
              onChange={(e) => setSlotsOpen(e.target.value)}
              className="w-24 rounded-xl border border-border bg-surface px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <Button variant="gradient" onClick={() => openMutation.mutate()} disabled={openMutation.isPending}>
              {openMutation.isPending ? "Opening…" : "Open slot"}
            </Button>
          </div>
        </Card>
      )}

      {canCancel && (
        <Button
          variant="secondary"
          pill
          onClick={() => cancelMutation.mutate()}
          disabled={cancelMutation.isPending}
          className="w-full text-red-600"
        >
          {cancelMutation.isPending ? "Cancelling…" : "Cancel booking"}
        </Button>
      )}

      {booking.status === "completed" && otherPlayers.length > 0 && (
        <Card className="space-y-3">
          <p className="text-sm font-semibold">Rate your teammates</p>
          {otherPlayers.map((uid) => (
            <RatingForm
              key={uid}
              bookingId={bookingId}
              ratedUid={uid}
              onRated={() => setRatedUids((prev) => [...prev, uid])}
            />
          ))}
        </Card>
      )}
    </div>
  );
}

function normalizePhone(phone: string): string {
  const digits = phone.replace(/\D/g, "");
  return digits.length === 10 ? `91${digits}` : digits;
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
    <div className="space-y-1.5 border-t border-border pt-3 first:border-t-0 first:pt-0">
      <p className="text-sm text-ink-muted font-mono">{ratedUid.slice(0, 8)}…</p>
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((n) => (
          <button key={n} onClick={() => setRating(n)}>
            <Star
              size={20}
              className={n <= rating ? "fill-amber-400 text-amber-400" : "text-ink-muted/40"}
            />
          </button>
        ))}
      </div>
      <input
        placeholder="Comment (optional)"
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        className="w-full rounded-xl border border-border bg-surface px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
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
