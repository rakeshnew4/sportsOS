"use client";

import { useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CalendarDays, MapPin, Users2, Zap } from "lucide-react";
import {
  cancelMatchRequest,
  createMatchRequest,
  joinMatch,
  listMatchRequests,
  listOpenMatches,
} from "@/lib/api/matches";
import { listCourts, listVenues } from "@/lib/api/venues";
import { queryKeys } from "@/lib/queryKeys";
import { toISODate } from "@/lib/date";
import { useSession } from "@/components/providers/SessionProvider";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { FootballSpinner } from "@/components/ui/FootballSpinner";
import { SportFilterChips } from "@/components/ui/SportFilterChips";
import { ApiError } from "@/lib/api/client";
import { getSportTheme, sportLabel } from "@/lib/sportTheme";

type Tab = "open" | "queue";

export default function PlayPage() {
  const [tab, setTab] = useState<Tab>("open");

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold">Play</h1>
        <p className="text-ink-muted text-sm">Join an open match or queue up to find players.</p>
      </div>

      <div className="flex gap-1 rounded-2xl bg-surface-muted p-1">
        {(["open", "queue"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`flex-1 rounded-xl py-2.5 text-sm font-semibold transition-colors ${
              tab === t
                ? "bg-gradient-to-r from-brand-from to-brand-to text-white shadow-md shadow-indigo-600/20"
                : "text-ink-muted"
            }`}
          >
            {t === "open" ? "Open matches" : "Find players"}
          </button>
        ))}
      </div>

      {tab === "open" ? <OpenMatches /> : <FindPlayers />}
    </div>
  );
}

function OpenMatches() {
  const queryClient = useQueryClient();
  const [sport, setSport] = useState("");
  const [date, setDate] = useState("");
  const [error, setError] = useState<string | null>(null);

  const { data: matches, isLoading } = useQuery({
    queryKey: queryKeys.openMatches({ sport: sport || undefined, date: date || undefined }),
    queryFn: () => listOpenMatches({ sport: sport || undefined, date: date || undefined }),
  });

  const joinMutation = useMutation({
    mutationFn: ({ tenantId, bookingId }: { tenantId: string; bookingId: string }) =>
      joinMatch(tenantId, bookingId),
    onSuccess: () => {
      setError(null);
      queryClient.invalidateQueries({ queryKey: ["openMatches"] });
      queryClient.invalidateQueries({ queryKey: queryKeys.myBookings() });
    },
    onError: (err) => {
      setError(err instanceof ApiError ? err.message : "Could not join that match");
    },
  });

  return (
    <div className="space-y-4">
      <SportFilterChips value={sport} onChange={setSport} />
      <div className="flex items-center gap-2 rounded-full border border-border bg-surface px-4 py-2 w-fit">
        <CalendarDays size={15} strokeWidth={2.25} className="text-ink-muted shrink-0" />
        <input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          className="text-sm bg-transparent focus:outline-none"
        />
        {date && (
          <button onClick={() => setDate("")} className="text-xs font-medium text-ink-muted hover:text-foreground">
            Clear
          </button>
        )}
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}
      {isLoading && <FootballSpinner />}
      {matches && matches.length === 0 && (
        <EmptyState icon={Zap} title="No open matches right now" description="Check back later or start your own." />
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-3">
        {matches?.map((match) => {
          const theme = getSportTheme(match.sport);
          const Icon = theme.icon;
          const isFull = match.slots_open <= 0;
          const isNearlyFull = !isFull && match.slots_open <= 2;
          const joined = match.slots_total > 0 ? match.slots_total - match.slots_open : null;
          return (
            <Card key={match.booking_id} className="flex flex-col">
              <div className="flex items-center justify-between gap-2">
                <span className={`inline-flex items-center gap-1.5 text-xs font-semibold rounded-full px-2.5 py-1 ${theme.light}`}>
                  <Icon size={12} strokeWidth={2.5} />
                  {sportLabel(match.sport)}
                </span>
                {isFull ? (
                  <span className="shrink-0 text-xs font-semibold rounded-full px-2.5 py-1 bg-surface-muted text-ink-muted">
                    Full
                  </span>
                ) : isNearlyFull ? (
                  <span className="shrink-0 text-xs font-semibold rounded-full px-2.5 py-1 bg-amber-50 text-amber-700">
                    Only {match.slots_open} left
                  </span>
                ) : (
                  <span className={`shrink-0 text-xs font-semibold rounded-full px-2.5 py-1 ${theme.light}`}>
                    {match.slots_open} open
                  </span>
                )}
              </div>

              <div className="flex items-center gap-2 mt-3">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-surface-muted text-xs font-bold text-ink-muted">
                  {(match.created_by_name || "?").charAt(0).toUpperCase()}
                </span>
                <p className="text-sm font-medium truncate">{match.created_by_name || "A player"}</p>
                {joined !== null && (
                  <span className="text-xs text-ink-muted shrink-0">
                    · {joined}/{match.slots_total} joined
                  </span>
                )}
              </div>

              <p className="text-sm font-semibold mt-3">
                {match.date} · {match.start_time} – {match.end_time}
              </p>
              <p className="text-sm text-ink-muted flex items-center gap-1 mt-1 truncate">
                <MapPin size={13} className="shrink-0" /> {match.tenant_name}
              </p>
              {match.team_name && (
                <span className="inline-block mt-2 rounded-full bg-surface-muted px-2 py-0.5 text-[11px] font-medium text-ink-muted w-fit">
                  {match.team_name}
                </span>
              )}

              <div className="mt-auto pt-4 flex items-center justify-between">
                <div>
                  <p className="text-[10px] uppercase tracking-wide text-ink-muted font-semibold">Price</p>
                  <p className="text-sm font-bold">₹{match.price}</p>
                </div>
                <div className="flex items-center gap-3">
                  <Link
                    href={`/bookings/${match.booking_id}`}
                    className="text-xs font-medium text-ink-muted hover:text-foreground"
                  >
                    Details
                  </Link>
                  <Button
                    variant="gradient"
                    pill
                    onClick={() => joinMutation.mutate({ tenantId: match.tenant_id, bookingId: match.booking_id })}
                    disabled={joinMutation.isPending || isFull}
                    className="text-xs px-5 py-2.5"
                  >
                    {joinMutation.isPending ? "Joining…" : isFull ? "Full" : "Join"}
                  </Button>
                </div>
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}

function FindPlayers() {
  const session = useSession();
  const queryClient = useQueryClient();
  const [tenantId, setTenantId] = useState("");
  const [courtId, setCourtId] = useState("");
  const [date, setDate] = useState(() => toISODate(new Date()));
  const [startTime, setStartTime] = useState("18:00");
  const [endTime, setEndTime] = useState("19:00");
  const [error, setError] = useState<string | null>(null);

  const { data: venues } = useQuery({ queryKey: queryKeys.venues(), queryFn: () => listVenues() });
  const { data: courts } = useQuery({
    queryKey: queryKeys.courts(tenantId),
    queryFn: () => listCourts(tenantId),
    enabled: !!tenantId,
  });

  const { data: requests, isLoading } = useQuery({
    queryKey: queryKeys.matchRequests(tenantId, { courtId, date }),
    queryFn: () => listMatchRequests(tenantId, { courtId, date }),
    enabled: !!tenantId && !!courtId && !!date,
  });

  const queueMutation = useMutation({
    mutationFn: () => createMatchRequest(tenantId, { court_id: courtId, date, start_time: startTime, end_time: endTime }),
    onSuccess: () => {
      setError(null);
      queryClient.invalidateQueries({ queryKey: queryKeys.matchRequests(tenantId, { courtId, date }) });
      queryClient.invalidateQueries({ queryKey: queryKeys.myMatchRequests() });
      queryClient.invalidateQueries({ queryKey: queryKeys.myBookings() });
    },
    onError: (err) => {
      setError(err instanceof ApiError ? err.message : "Could not join the queue");
    },
  });

  const cancelMutation = useMutation({
    mutationFn: (requestId: string) => cancelMatchRequest(tenantId, requestId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.matchRequests(tenantId, { courtId, date }) });
      queryClient.invalidateQueries({ queryKey: queryKeys.myMatchRequests() });
    },
    onError: (err) => {
      setError(err instanceof ApiError ? err.message : "Could not cancel");
    },
  });

  return (
    <div className="space-y-4">
      <Card className="space-y-3">
        <p className="text-sm font-semibold">Queue for a match</p>
        <select
          value={tenantId}
          onChange={(e) => {
            setTenantId(e.target.value);
            setCourtId("");
          }}
          className="w-full rounded-full border border-border bg-surface px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="">Select venue…</option>
          {venues?.map((v) => (
            <option key={v.tenant_id} value={v.tenant_id}>
              {v.name} · {v.city}
            </option>
          ))}
        </select>
        <select
          value={courtId}
          onChange={(e) => setCourtId(e.target.value)}
          disabled={!tenantId}
          className="w-full rounded-full border border-border bg-surface px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
        >
          <option value="">Select court…</option>
          {courts?.map((c) => (
            <option key={c.court_id} value={c.court_id}>
              {c.name} · {sportLabel(c.sport)}
            </option>
          ))}
        </select>
        <div className="grid grid-cols-3 gap-2">
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="rounded-full border border-border bg-surface px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <input
            type="time"
            value={startTime}
            onChange={(e) => setStartTime(e.target.value)}
            className="rounded-full border border-border bg-surface px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <input
            type="time"
            value={endTime}
            onChange={(e) => setEndTime(e.target.value)}
            className="rounded-full border border-border bg-surface px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <Button
          variant="gradient"
          pill
          onClick={() => queueMutation.mutate()}
          disabled={!tenantId || !courtId || queueMutation.isPending}
          className="w-full"
        >
          {queueMutation.isPending ? "Joining queue…" : "Join queue"}
        </Button>
        {error && <p className="text-sm text-red-600">{error}</p>}
      </Card>

      {tenantId && courtId && (
        <div>
          <p className="text-sm font-semibold mb-2">Queue for this court/date</p>
          {isLoading && <FootballSpinner />}
          {requests && requests.length === 0 && (
            <EmptyState icon={Users2} title="No one queued yet" description="Be the first to start the queue." />
          )}
          <div className="space-y-2">
            {requests?.map((r) => {
              const pct = Math.min(100, Math.round((r.current_count / r.min_players) * 100));
              const isMe = r.uid === session.uid;
              return (
                <Card key={r.request_id}>
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm font-medium">
                      {r.start_time} – {r.end_time}
                      {isMe && <span className="text-indigo-600"> (you)</span>}
                    </p>
                    {isMe && r.status === "waiting" && (
                      <button
                        onClick={() => cancelMutation.mutate(r.request_id)}
                        disabled={cancelMutation.isPending}
                        className="text-xs font-medium text-red-600"
                      >
                        Cancel
                      </button>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
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
                </Card>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
