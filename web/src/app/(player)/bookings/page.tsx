"use client";

import { useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CalendarX2, IndianRupee, MapPin, Users2 } from "lucide-react";
import { listMyBookings } from "@/lib/api/bookings";
import { cancelMatchRequest, listMyMatchRequests } from "@/lib/api/matches";
import { queryKeys } from "@/lib/queryKeys";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import { SkeletonCard } from "@/components/ui/Skeleton";
import { getSportTheme, sportLabel } from "@/lib/sportTheme";
import { ApiError } from "@/lib/api/client";
import type { MatchRequestResponse } from "@/lib/types";

type Tab = "bookings" | "queue";

export default function BookingsPage() {
  const [tab, setTab] = useState<Tab>("bookings");

  const { data: myMatchRequests } = useQuery({
    queryKey: queryKeys.myMatchRequests(),
    queryFn: listMyMatchRequests,
  });
  const waitingCount = myMatchRequests?.filter((r) => r.status === "waiting").length ?? 0;

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold">My bookings</h1>
        <p className="text-ink-muted text-sm">Courts you&apos;ve booked, and matches you&apos;re queued for.</p>
      </div>

      <div className="flex gap-1 rounded-2xl bg-surface-muted p-1">
        {(["bookings", "queue"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`flex-1 rounded-xl py-2.5 text-sm font-semibold transition-colors ${
              tab === t
                ? "bg-gradient-to-r from-brand-from to-brand-to text-white shadow-md shadow-indigo-600/20"
                : "text-ink-muted"
            }`}
          >
            {t === "bookings" ? "Bookings" : `Queue${waitingCount > 0 ? ` (${waitingCount})` : ""}`}
          </button>
        ))}
      </div>

      {tab === "bookings" ? <MyBookings /> : <MyQueue requests={myMatchRequests} />}
    </div>
  );
}

function MyBookings() {
  const { data: bookings, isLoading } = useQuery({
    queryKey: queryKeys.myBookings(),
    queryFn: listMyBookings,
  });

  const sorted = bookings?.slice().sort((a, b) => (a.date < b.date ? 1 : -1));

  return (
    <div className="space-y-4">
      {isLoading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-3">
          <SkeletonCard />
          <SkeletonCard />
        </div>
      )}
      {sorted && sorted.length === 0 && (
        <EmptyState icon={CalendarX2} title="No bookings yet" description="Go book a court to get started." />
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-3">
        {sorted?.map((booking) => {
          const theme = getSportTheme(booking.sport);
          return (
            <Link key={booking.booking_id} href={`/bookings/${booking.booking_id}`}>
              <Card accentGradient={theme.gradient} interactive>
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-semibold">{sportLabel(booking.sport)}</p>
                    <p className="text-sm text-ink-muted">
                      {booking.date} · {booking.start_time} – {booking.end_time}
                    </p>
                    {booking.tenant_name && (
                      <p className="text-xs text-ink-muted flex items-center gap-1 mt-1 truncate">
                        <MapPin size={12} className="shrink-0" /> {booking.tenant_name}
                        {booking.court_name ? ` · ${booking.court_name}` : ""}
                      </p>
                    )}
                    {booking.team_name && (
                      <p className="text-xs text-ink-muted mt-1">{booking.team_name}</p>
                    )}
                  </div>
                  <Badge status={booking.status}>{booking.status.replace("_", " ")}</Badge>
                </div>
                <p className="text-sm font-semibold mt-2 flex items-center gap-0.5">
                  <IndianRupee size={13} />
                  {booking.price}
                </p>
              </Card>
            </Link>
          );
        })}
      </div>
    </div>
  );
}

function MyQueue({ requests }: { requests: MatchRequestResponse[] | undefined }) {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);

  const cancelMutation = useMutation({
    mutationFn: (r: MatchRequestResponse) => cancelMatchRequest(r.tenant_id, r.request_id),
    onSuccess: () => {
      setError(null);
      queryClient.invalidateQueries({ queryKey: queryKeys.myMatchRequests() });
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not cancel"),
  });

  const visible = requests?.filter((r) => r.status !== "cancelled");

  return (
    <div className="space-y-3">
      {error && <p className="text-sm text-red-600">{error}</p>}

      {!requests && (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-3">
          <SkeletonCard />
          <SkeletonCard />
        </div>
      )}
      {visible && visible.length === 0 && (
        <EmptyState
          icon={Users2}
          title="You're not queued for anything"
          description="Head to Play → Find players to queue up for a match."
        />
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-3">
        {visible?.map((r) => {
          const theme = getSportTheme(r.sport);
          const Icon = theme.icon;
          const pct = Math.min(100, Math.round((r.current_count / r.min_players) * 100));
          return (
            <Card key={r.request_id} className="flex flex-col">
              <div className="flex items-center justify-between gap-2">
                <span className={`inline-flex items-center gap-1.5 text-xs font-semibold rounded-full px-2.5 py-1 ${theme.light}`}>
                  <Icon size={12} strokeWidth={2.5} />
                  {sportLabel(r.sport)}
                </span>
                <Badge status={r.status}>{r.status}</Badge>
              </div>

              <p className="text-sm font-semibold mt-3">
                {r.date} · {r.start_time} – {r.end_time}
              </p>
              {r.tenant_name && (
                <p className="text-sm text-ink-muted flex items-center gap-1 mt-1 truncate">
                  <MapPin size={13} className="shrink-0" /> {r.tenant_name}
                  {r.court_name ? ` · ${r.court_name}` : ""}
                </p>
              )}

              {r.status === "waiting" ? (
                <>
                  <div className="flex items-center gap-2 mt-3">
                    <div className="flex-1 h-2 rounded-full bg-surface-muted overflow-hidden">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-brand-from to-brand-to transition-all"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <span className="text-xs font-semibold text-ink-muted whitespace-nowrap">
                      {r.current_count}/{r.min_players}
                    </span>
                  </div>
                  <button
                    onClick={() => cancelMutation.mutate(r)}
                    disabled={cancelMutation.isPending}
                    className="mt-auto pt-4 text-xs font-medium text-red-600 text-left disabled:opacity-50"
                  >
                    Leave queue
                  </button>
                </>
              ) : (
                r.matched_booking_id && (
                  <Link
                    href={`/bookings/${r.matched_booking_id}`}
                    className="mt-auto pt-4 text-xs font-medium text-indigo-600"
                  >
                    View booking →
                  </Link>
                )
              )}
            </Card>
          );
        })}
      </div>
    </div>
  );
}
