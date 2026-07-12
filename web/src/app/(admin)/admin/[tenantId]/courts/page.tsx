"use client";

import { use, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createCourt, listCourts, updateCourt } from "@/lib/api/venues";
import { queryKeys } from "@/lib/queryKeys";
import { Button } from "@/components/ui/Button";
import { FootballSpinner } from "@/components/ui/FootballSpinner";
import { ApiError } from "@/lib/api/client";
import type { CourtResponse } from "@/lib/types";

export default function CourtsPage({ params }: { params: Promise<{ tenantId: string }> }) {
  const { tenantId } = use(params);
  const queryClient = useQueryClient();
  const [isNewVenue] = useState(() => typeof window !== "undefined" && new URLSearchParams(window.location.search).get("new") === "1");
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(isNewVenue);
  const [name, setName] = useState("");
  const [sport, setSport] = useState("");
  const [hourlyPrice, setHourlyPrice] = useState("");
  const [openTime, setOpenTime] = useState("06:00");
  const [closeTime, setCloseTime] = useState("23:00");
  const [minPlayers, setMinPlayers] = useState("");

  const { data: courts, isLoading } = useQuery({
    queryKey: queryKeys.courts(tenantId),
    queryFn: () => listCourts(tenantId),
  });

  const createMutation = useMutation({
    mutationFn: () =>
      createCourt(tenantId, {
        name,
        sport,
        hourly_price: Number(hourlyPrice),
        open_time: openTime,
        close_time: closeTime,
        min_players: minPlayers ? Number(minPlayers) : undefined,
      }),
    onSuccess: () => {
      setError(null);
      setName("");
      setSport("");
      setHourlyPrice("");
      setMinPlayers("");
      setShowCreate(false);
      queryClient.invalidateQueries({ queryKey: queryKeys.courts(tenantId) });
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not create court"),
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Courts</h1>
        <Button variant="secondary" onClick={() => setShowCreate((s) => !s)}>
          {showCreate ? "Cancel" : "+ Add court"}
        </Button>
      </div>

      {isNewVenue && courts?.length === 0 && (
        <div className="rounded-xl bg-emerald-50 border border-emerald-200 px-4 py-3">
          <p className="text-sm text-emerald-800">
            Venue created. Add at least one court below with its hourly price and open/close hours —
            players can&apos;t book until a court exists.
          </p>
        </div>
      )}

      {error && <p className="text-sm text-red-600">{error}</p>}

      {showCreate && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            createMutation.mutate();
          }}
          className="rounded-2xl border border-neutral-200 bg-white p-4 space-y-3"
        >
          <input
            placeholder="Court name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
          <input
            placeholder="Sport"
            value={sport}
            onChange={(e) => setSport(e.target.value)}
            required
            className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
          <input
            type="number"
            placeholder="Hourly price"
            value={hourlyPrice}
            onChange={(e) => setHourlyPrice(e.target.value)}
            required
            className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
          <div className="grid grid-cols-2 gap-2">
            <input
              type="time"
              value={openTime}
              onChange={(e) => setOpenTime(e.target.value)}
              className="rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
            <input
              type="time"
              value={closeTime}
              onChange={(e) => setCloseTime(e.target.value)}
              className="rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>
          <div>
            <input
              type="number"
              min={1}
              placeholder="Min players to auto-confirm queue (optional)"
              value={minPlayers}
              onChange={(e) => setMinPlayers(e.target.value)}
              className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
            <p className="text-xs text-neutral-400 mt-1">
              When this many players are queued for the same slot in &quot;Join Match&quot;, we auto-confirm a
              booking and split the cost. Leave blank to use the sport&apos;s default.
            </p>
          </div>
          <Button type="submit" disabled={createMutation.isPending} className="w-full">
            {createMutation.isPending ? "Creating…" : "Create court"}
          </Button>
        </form>
      )}

      {isLoading && <FootballSpinner />}

      {!isLoading && courts?.length === 0 && !showCreate && (
        <div className="rounded-xl border border-dashed border-neutral-300 px-4 py-6 text-center">
          <p className="text-sm font-medium text-neutral-700">No courts yet</p>
          <p className="text-xs text-neutral-500 mt-1">
            Add a court to set its sport, hourly price, and open/close hours.
          </p>
          <Button variant="secondary" onClick={() => setShowCreate(true)} className="mt-3">
            + Add your first court
          </Button>
        </div>
      )}

      <div className="space-y-2">
        {courts?.map((court) => (
          <CourtRow key={court.court_id} tenantId={tenantId} court={court} onError={setError} />
        ))}
      </div>
    </div>
  );
}

function CourtRow({
  tenantId,
  court,
  onError,
}: {
  tenantId: string;
  court: CourtResponse;
  onError: (message: string) => void;
}) {
  const queryClient = useQueryClient();
  const [minPlayers, setMinPlayers] = useState(court.min_players?.toString() ?? "");

  const toggleActiveMutation = useMutation({
    mutationFn: () => updateCourt(tenantId, court.court_id, { is_active: !court.is_active }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.courts(tenantId) }),
    onError: (err) => onError(err instanceof ApiError ? err.message : "Could not update court"),
  });

  const minPlayersMutation = useMutation({
    mutationFn: () => updateCourt(tenantId, court.court_id, { min_players: Number(minPlayers) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.courts(tenantId) }),
    onError: (err) => onError(err instanceof ApiError ? err.message : "Could not update court"),
  });

  const minPlayersDirty = minPlayers !== (court.min_players?.toString() ?? "");

  return (
    <div className="rounded-xl border border-neutral-200 bg-white px-4 py-3 space-y-2">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-neutral-900">{court.name}</p>
          <p className="text-xs text-neutral-400">
            {court.sport.replace("_", " ")} · ₹{court.hourly_price}/hr · {court.open_time}–{court.close_time}
          </p>
        </div>
        <Button
          variant="secondary"
          onClick={() => toggleActiveMutation.mutate()}
          disabled={toggleActiveMutation.isPending}
          className={court.is_active ? "text-neutral-700" : "text-neutral-400"}
        >
          {court.is_active ? "Active" : "Inactive"}
        </Button>
      </div>
      <div className="flex items-center gap-2 pt-2 border-t border-neutral-100">
        <label className="text-xs text-neutral-500 shrink-0">Min players to auto-confirm:</label>
        <input
          type="number"
          min={1}
          placeholder="Sport default"
          value={minPlayers}
          onChange={(e) => setMinPlayers(e.target.value)}
          className="w-28 rounded-lg border border-neutral-300 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
        />
        {minPlayersDirty && (
          <Button
            variant="secondary"
            onClick={() => minPlayersMutation.mutate()}
            disabled={minPlayersMutation.isPending || !minPlayers}
            className="text-xs px-3 py-1.5"
          >
            {minPlayersMutation.isPending ? "Saving…" : "Save"}
          </Button>
        )}
      </div>
    </div>
  );
}
