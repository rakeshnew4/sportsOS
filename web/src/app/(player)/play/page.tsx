"use client";

import { useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Users2, Zap } from "lucide-react";
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
import { SkeletonCard } from "@/components/ui/Skeleton";
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
      <div className="flex gap-2">
        <input
          placeholder="Sport"
          value={sport}
          onChange={(e) => setSport(e.target.value)}
          className="flex-1 rounded-xl border border-border bg-surface px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          className="rounded-xl border border-border bg-surface px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}
      {isLoading && (
        <div className="space-y-3">
          <SkeletonCard />
          <SkeletonCard />
        </div>
      )}
      {matches && matches.length === 0 && (
        <EmptyState icon={Zap} title="No open matches right now" description="Check back later or start your own." />
      )}

      <div className="space-y-3">
        {matches?.map((match) => {
          const theme = getSportTheme(match.sport);
          return (
            <Card key={match.booking_id} accentGradient={theme.gradient}>
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-semibold">{sportLabel(match.sport)}</p>
                  <p className="text-sm text-ink-muted">{match.tenant_name}</p>
                  <p className="text-sm text-ink-muted">
                    {match.date} · {match.start_time} – {match.end_time}
                  </p>
                </div>
                <span className={`text-xs font-semibold rounded-full px-2.5 py-1 ${theme.light}`}>
                  {match.slots_open} open
                </span>
              </div>
              <div className="mt-3 flex items-center justify-between">
                <Link
                  href={`/bookings/${match.booking_id}`}
                  className="text-xs font-medium text-ink-muted hover:text-foreground"
                >
                  View details
                </Link>
                <Button
                  variant="gradient"
                  onClick={() => joinMutation.mutate({ tenantId: match.tenant_id, bookingId: match.booking_id })}
                  disabled={joinMutation.isPending}
                  className="text-xs px-4 py-2"
                >
                  {joinMutation.isPending ? "Joining…" : "Join"}
                </Button>
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
    },
    onError: (err) => {
      setError(err instanceof ApiError ? err.message : "Could not join the queue");
    },
  });

  const cancelMutation = useMutation({
    mutationFn: (requestId: string) => cancelMatchRequest(tenantId, requestId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.matchRequests(tenantId, { courtId, date }) });
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
          className="w-full rounded-xl border border-border bg-surface px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
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
          className="w-full rounded-xl border border-border bg-surface px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
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
            className="rounded-xl border border-border bg-surface px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <input
            type="time"
            value={startTime}
            onChange={(e) => setStartTime(e.target.value)}
            className="rounded-xl border border-border bg-surface px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <input
            type="time"
            value={endTime}
            onChange={(e) => setEndTime(e.target.value)}
            className="rounded-xl border border-border bg-surface px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <Button
          variant="gradient"
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
          {isLoading && <SkeletonCard />}
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
