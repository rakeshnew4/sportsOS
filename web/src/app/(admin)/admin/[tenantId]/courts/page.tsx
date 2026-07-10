"use client";

import { use, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createCourt, listCourts, updateCourt } from "@/lib/api/venues";
import { queryKeys } from "@/lib/queryKeys";
import { Button } from "@/components/ui/Button";
import { ApiError } from "@/lib/api/client";

export default function CourtsPage({ params }: { params: Promise<{ tenantId: string }> }) {
  const { tenantId } = use(params);
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [sport, setSport] = useState("");
  const [hourlyPrice, setHourlyPrice] = useState("");
  const [openTime, setOpenTime] = useState("06:00");
  const [closeTime, setCloseTime] = useState("23:00");

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
      }),
    onSuccess: () => {
      setError(null);
      setName("");
      setSport("");
      setHourlyPrice("");
      setShowCreate(false);
      queryClient.invalidateQueries({ queryKey: queryKeys.courts(tenantId) });
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not create court"),
  });

  const toggleActiveMutation = useMutation({
    mutationFn: ({ courtId, isActive }: { courtId: string; isActive: boolean }) =>
      updateCourt(tenantId, courtId, { is_active: isActive }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.courts(tenantId) }),
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not update court"),
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Courts</h1>
        <Button variant="secondary" onClick={() => setShowCreate((s) => !s)}>
          {showCreate ? "Cancel" : "+ Add court"}
        </Button>
      </div>

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
          <Button type="submit" disabled={createMutation.isPending} className="w-full">
            {createMutation.isPending ? "Creating…" : "Create court"}
          </Button>
        </form>
      )}

      {isLoading && <p className="text-sm text-neutral-500">Loading…</p>}

      <div className="space-y-2">
        {courts?.map((court) => (
          <div
            key={court.court_id}
            className="flex items-center justify-between rounded-xl border border-neutral-200 bg-white px-4 py-3"
          >
            <div>
              <p className="text-sm font-medium text-neutral-900">{court.name}</p>
              <p className="text-xs text-neutral-400">
                {court.sport.replace("_", " ")} · ₹{court.hourly_price}/hr · {court.open_time}–{court.close_time}
              </p>
            </div>
            <Button
              variant="secondary"
              onClick={() =>
                toggleActiveMutation.mutate({ courtId: court.court_id, isActive: !court.is_active })
              }
              disabled={toggleActiveMutation.isPending}
              className={court.is_active ? "text-neutral-700" : "text-neutral-400"}
            >
              {court.is_active ? "Active" : "Inactive"}
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
}
