"use client";

import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { sendBroadcast, type BroadcastTarget } from "@/lib/api/broadcast";
import { listVenues, listCourts } from "@/lib/api/venues";
import { listTeams } from "@/lib/api/teams";
import { queryKeys } from "@/lib/queryKeys";
import { ALL_SPORTS, sportLabel } from "@/lib/sportTheme";
import { Button } from "@/components/ui/Button";
import { ApiError } from "@/lib/api/client";

const TARGETS: { value: BroadcastTarget; label: string; description: string }[] = [
  { value: "all_players", label: "All players", description: "Every player account on the platform." },
  { value: "all_admins", label: "All admins", description: "Every venue owner/staff login account." },
  { value: "sport", label: "By sport", description: "Everyone who's booked or played a given sport." },
  { value: "court", label: "By court", description: "Everyone who's booked a specific court." },
  { value: "team", label: "By team", description: "A specific team's captain and members." },
];

export default function BroadcastPage() {
  const [target, setTarget] = useState<BroadcastTarget>("all_players");
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [sport, setSport] = useState("");
  const [tenantId, setTenantId] = useState("");
  const [courtId, setCourtId] = useState("");
  const [teamId, setTeamId] = useState("");
  const [city, setCity] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<number | null>(null);

  const { data: venues } = useQuery({ queryKey: queryKeys.venues(), queryFn: () => listVenues() });
  const { data: courts } = useQuery({
    queryKey: queryKeys.courts(tenantId),
    queryFn: () => listCourts(tenantId),
    enabled: target === "court" && Boolean(tenantId),
  });
  const { data: teams } = useQuery({
    queryKey: queryKeys.teams(),
    queryFn: () => listTeams(),
    enabled: target === "team",
  });

  const sendMutation = useMutation({
    mutationFn: () =>
      sendBroadcast({
        target,
        title,
        body,
        sport: target === "sport" ? sport : undefined,
        court_id: target === "court" ? courtId : undefined,
        team_id: target === "team" ? teamId : undefined,
        tenant_id: ["all_players", "all_admins", "sport"].includes(target) && tenantId ? tenantId : undefined,
        city: ["all_players", "sport"].includes(target) && city ? city : undefined,
      }),
    onSuccess: (data) => {
      setResult(data.recipient_count);
      setError(null);
    },
    onError: (err) => {
      setResult(null);
      setError(err instanceof ApiError ? err.message : "Could not send broadcast");
    },
  });

  const canSubmit =
    title.trim() &&
    body.trim() &&
    (target !== "sport" || sport) &&
    (target !== "court" || courtId) &&
    (target !== "team" || teamId);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold">Broadcast notification</h1>
        <p className="text-neutral-500 text-sm">
          Send an in-app (and push, where enabled) notification to a segment of users.
        </p>
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          sendMutation.mutate();
        }}
        className="rounded-2xl border border-neutral-200 bg-white p-4 space-y-4"
      >
        <div>
          <p className="text-sm font-semibold text-neutral-700 mb-2">Send to</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {TARGETS.map((t) => (
              <button
                key={t.value}
                type="button"
                onClick={() => setTarget(t.value)}
                className={`text-left rounded-lg border px-3 py-2 text-sm transition-colors ${
                  target === t.value
                    ? "border-emerald-500 bg-emerald-50 text-emerald-900"
                    : "border-neutral-200 text-neutral-600"
                }`}
              >
                <p className="font-medium">{t.label}</p>
                <p className="text-xs text-neutral-500">{t.description}</p>
              </button>
            ))}
          </div>
        </div>

        {target === "sport" && (
          <select
            value={sport}
            onChange={(e) => setSport(e.target.value)}
            required
            className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="">Select a sport…</option>
            {ALL_SPORTS.map((s) => (
              <option key={s} value={s}>
                {sportLabel(s)}
              </option>
            ))}
          </select>
        )}

        {target === "court" && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <select
              value={tenantId}
              onChange={(e) => {
                setTenantId(e.target.value);
                setCourtId("");
              }}
              required
              className="rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="">Select a venue…</option>
              {venues?.map((v) => (
                <option key={v.tenant_id} value={v.tenant_id}>
                  {v.name}
                </option>
              ))}
            </select>
            <select
              value={courtId}
              onChange={(e) => setCourtId(e.target.value)}
              required
              disabled={!tenantId}
              className="rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 disabled:opacity-50"
            >
              <option value="">Select a court…</option>
              {courts?.map((c) => (
                <option key={c.court_id} value={c.court_id}>
                  {c.name} ({sportLabel(c.sport)})
                </option>
              ))}
            </select>
          </div>
        )}

        {target === "team" && (
          <select
            value={teamId}
            onChange={(e) => setTeamId(e.target.value)}
            required
            className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="">Select a team…</option>
            {teams?.map((t) => (
              <option key={t.team_id} value={t.team_id}>
                {t.team_name} ({sportLabel(t.sport)})
              </option>
            ))}
          </select>
        )}

        {["all_players", "all_admins", "sport"].includes(target) && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <select
              value={tenantId}
              onChange={(e) => setTenantId(e.target.value)}
              className="rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="">All venues</option>
              {venues?.map((v) => (
                <option key={v.tenant_id} value={v.tenant_id}>
                  {v.name}
                </option>
              ))}
            </select>
            {target !== "all_admins" && (
              <input
                placeholder="City filter (optional)"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                className="rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            )}
          </div>
        )}

        <input
          placeholder="Notification title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
          className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
        />
        <textarea
          placeholder="Notification body"
          value={body}
          onChange={(e) => setBody(e.target.value)}
          required
          rows={3}
          className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
        />

        {error && <p className="text-sm text-red-600">{error}</p>}
        <Button type="submit" disabled={!canSubmit || sendMutation.isPending}>
          {sendMutation.isPending ? "Sending…" : "Send broadcast"}
        </Button>
      </form>

      {result !== null && (
        <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-3 text-sm text-emerald-900">
          Sent to {result} recipient{result === 1 ? "" : "s"}.
        </div>
      )}
    </div>
  );
}
