"use client";

import { useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
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
import { ApiError } from "@/lib/api/client";

type Tab = "open" | "queue";

export default function PlayPage() {
  const [tab, setTab] = useState<Tab>("open");

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold">Play</h1>
        <p className="text-neutral-500 text-sm">Join an open match or queue up to find players.</p>
      </div>

      <div className="flex gap-2 rounded-xl bg-neutral-100 p-1">
        {(["open", "queue"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`flex-1 rounded-lg py-2 text-sm font-medium transition-colors ${
              tab === t ? "bg-white shadow-sm text-neutral-900" : "text-neutral-500"
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
          className="flex-1 rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
        />
        <input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          className="rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
        />
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}
      {isLoading && <p className="text-sm text-neutral-500">Loading…</p>}
      {matches && matches.length === 0 && (
        <p className="text-sm text-neutral-500">No open matches right now.</p>
      )}

      <div className="space-y-3">
        {matches?.map((match) => (
          <div
            key={match.booking_id}
            className="rounded-2xl border border-neutral-200 bg-white p-4 shadow-sm"
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="font-semibold text-neutral-900">{match.sport.replace("_", " ")}</p>
                <p className="text-sm text-neutral-500">{match.tenant_name}</p>
                <p className="text-sm text-neutral-500">
                  {match.date} · {match.start_time} – {match.end_time}
                </p>
              </div>
              <span className="text-xs font-medium rounded-full px-2 py-1 bg-emerald-50 text-emerald-700">
                {match.slots_open} open
              </span>
            </div>
            <div className="mt-3 flex items-center justify-between">
              <Link
                href={`/bookings/${match.booking_id}`}
                className="text-xs font-medium text-neutral-500 hover:text-neutral-800"
              >
                View details
              </Link>
              <Button
                onClick={() => joinMutation.mutate({ tenantId: match.tenant_id, bookingId: match.booking_id })}
                disabled={joinMutation.isPending}
              >
                {joinMutation.isPending ? "Joining…" : "Join"}
              </Button>
            </div>
          </div>
        ))}
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
      <div className="rounded-2xl border border-neutral-200 bg-white p-4 space-y-3">
        <p className="text-sm font-semibold text-neutral-700">Queue for a match</p>
        <select
          value={tenantId}
          onChange={(e) => {
            setTenantId(e.target.value);
            setCourtId("");
          }}
          className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
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
          className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
        >
          <option value="">Select court…</option>
          {courts?.map((c) => (
            <option key={c.court_id} value={c.court_id}>
              {c.name} · {c.sport.replace("_", " ")}
            </option>
          ))}
        </select>
        <div className="grid grid-cols-3 gap-2">
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
          <input
            type="time"
            value={startTime}
            onChange={(e) => setStartTime(e.target.value)}
            className="rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
          <input
            type="time"
            value={endTime}
            onChange={(e) => setEndTime(e.target.value)}
            className="rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
        </div>
        <Button
          onClick={() => queueMutation.mutate()}
          disabled={!tenantId || !courtId || queueMutation.isPending}
          className="w-full"
        >
          {queueMutation.isPending ? "Joining queue…" : "Join queue"}
        </Button>
        {error && <p className="text-sm text-red-600">{error}</p>}
      </div>

      {tenantId && courtId && (
        <div>
          <p className="text-sm font-semibold text-neutral-700 mb-2">Queue for this court/date</p>
          {isLoading && <p className="text-sm text-neutral-500">Loading…</p>}
          {requests && requests.length === 0 && (
            <p className="text-sm text-neutral-500">No one queued yet — be the first.</p>
          )}
          <div className="space-y-2">
            {requests?.map((r) => (
              <div
                key={r.request_id}
                className="flex items-center justify-between rounded-xl border border-neutral-200 bg-white px-4 py-3"
              >
                <div>
                  <p className="text-sm font-medium text-neutral-900">
                    {r.start_time} – {r.end_time} · {r.current_count}/{r.min_players} players
                    {r.uid === session.uid && <span className="text-emerald-600"> (you)</span>}
                  </p>
                  <p className="text-xs text-neutral-400">{r.status}</p>
                </div>
                {r.uid === session.uid && r.status === "waiting" && (
                  <Button
                    variant="secondary"
                    onClick={() => cancelMutation.mutate(r.request_id)}
                    disabled={cancelMutation.isPending}
                  >
                    Cancel
                  </Button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
