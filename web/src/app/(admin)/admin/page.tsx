"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQueries, useQueryClient } from "@tanstack/react-query";
import { createVenue, getVenue } from "@/lib/api/venues";
import { queryKeys } from "@/lib/queryKeys";
import { useSession } from "@/components/providers/SessionProvider";
import { Button } from "@/components/ui/Button";
import { ApiError } from "@/lib/api/client";

export default function MyVenuesPage() {
  const session = useSession();
  const router = useRouter();
  const queryClient = useQueryClient();
  const tenantIds = Array.from(new Set([...session.owner_of, ...session.staff_of]));

  const venueQueries = useQueries({
    queries: tenantIds.map((tenantId) => ({
      queryKey: queryKeys.venue(tenantId),
      queryFn: () => getVenue(tenantId),
    })),
  });

  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [city, setCity] = useState("");
  const [lat, setLat] = useState("");
  const [lng, setLng] = useState("");
  const [sports, setSports] = useState("");
  const [error, setError] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: () =>
      createVenue({
        name,
        city,
        geo: { lat: Number(lat), lng: Number(lng) },
        sports: sports.split(",").map((s) => s.trim()).filter(Boolean),
      }),
    onSuccess: (venue) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.venue(venue.tenant_id) });
      router.push(`/admin/${venue.tenant_id}`);
      router.refresh();
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not create venue"),
  });

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold">My venues</h1>
        <p className="text-neutral-500 text-sm">Manage venues you own or staff.</p>
      </div>

      <div className="space-y-3">
        {tenantIds.map((tenantId, i) => {
          const venue = venueQueries[i].data;
          if (!venue) return null;
          return (
            <Link
              key={tenantId}
              href={`/admin/${tenantId}`}
              className="block rounded-2xl border border-neutral-200 bg-white p-4 shadow-sm hover:border-neutral-300"
            >
              <p className="font-semibold text-neutral-900">{venue.name}</p>
              <p className="text-sm text-neutral-500">{venue.city}</p>
              <p className="text-xs text-neutral-400 mt-1">
                {session.owner_of.includes(tenantId) ? "Owner" : "Staff"}
              </p>
            </Link>
          );
        })}
        {tenantIds.length === 0 && (
          <p className="text-sm text-neutral-500">You don't manage any venues yet.</p>
        )}
      </div>

      {!showCreate && (
        <Button variant="secondary" onClick={() => setShowCreate(true)} className="w-full">
          + Create a venue
        </Button>
      )}

      {showCreate && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            createMutation.mutate();
          }}
          className="rounded-2xl border border-neutral-200 bg-white p-4 space-y-3"
        >
          <p className="text-sm font-semibold text-neutral-700">Create a venue</p>
          <input
            placeholder="Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
          <input
            placeholder="City"
            value={city}
            onChange={(e) => setCity(e.target.value)}
            required
            className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
          <div className="grid grid-cols-2 gap-2">
            <input
              placeholder="Latitude"
              type="number"
              step="any"
              value={lat}
              onChange={(e) => setLat(e.target.value)}
              required
              className="rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
            <input
              placeholder="Longitude"
              type="number"
              step="any"
              value={lng}
              onChange={(e) => setLng(e.target.value)}
              required
              className="rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>
          <input
            placeholder="Sports (comma separated, e.g. badminton, tennis)"
            value={sports}
            onChange={(e) => setSports(e.target.value)}
            required
            className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
          {error && <p className="text-sm text-red-600">{error}</p>}
          <div className="flex gap-2">
            <Button type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending ? "Creating…" : "Create venue"}
            </Button>
            <Button type="button" variant="ghost" onClick={() => setShowCreate(false)}>
              Cancel
            </Button>
          </div>
        </form>
      )}

      <div className="rounded-xl bg-neutral-100 p-3">
        <p className="text-xs text-neutral-500">
          Your uid (share with a venue owner to be added as staff):
        </p>
        <p className="text-xs font-mono text-neutral-700 break-all">{session.uid}</p>
      </div>
    </div>
  );
}
