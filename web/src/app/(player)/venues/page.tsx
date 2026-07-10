"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { listVenues } from "@/lib/api/venues";
import { queryKeys } from "@/lib/queryKeys";

const SPORTS = ["badminton", "tennis", "table_tennis", "cricket", "volleyball"];

export default function VenuesPage() {
  const [sport, setSport] = useState<string | null>(null);
  const [city, setCity] = useState("");

  const { data: venues, isLoading } = useQuery({
    queryKey: queryKeys.venues({ city: city || undefined, sport: sport || undefined }),
    queryFn: () => listVenues({ city: city || undefined, sport: sport || undefined }),
  });

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold">Find a venue</h1>
        <p className="text-neutral-500 text-sm">Pick a sport and city to see what's nearby.</p>
      </div>

      <input
        type="text"
        placeholder="City"
        value={city}
        onChange={(e) => setCity(e.target.value)}
        className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
      />

      <div className="flex flex-wrap gap-2">
        {SPORTS.map((s) => (
          <button
            key={s}
            onClick={() => setSport(sport === s ? null : s)}
            className={`rounded-full px-3 py-1.5 text-xs font-medium border transition-colors ${
              sport === s
                ? "bg-emerald-600 text-white border-emerald-600"
                : "bg-white text-neutral-600 border-neutral-300"
            }`}
          >
            {s.replace("_", " ")}
          </button>
        ))}
      </div>

      {isLoading && <p className="text-sm text-neutral-500">Loading venues…</p>}
      {venues && venues.length === 0 && (
        <p className="text-sm text-neutral-500">No venues match those filters.</p>
      )}

      <div className="space-y-3">
        {venues?.map((venue) => (
          <Link
            key={venue.tenant_id}
            href={`/venues/${venue.tenant_id}`}
            className="block rounded-2xl border border-neutral-200 bg-white p-4 shadow-sm hover:shadow-md transition-shadow"
          >
            <p className="font-semibold text-neutral-900">{venue.name}</p>
            <p className="text-sm text-neutral-500">{venue.city}</p>
            <div className="flex flex-wrap gap-1.5 mt-2">
              {venue.sports.map((s) => (
                <span key={s} className="text-xs bg-neutral-100 text-neutral-600 rounded-full px-2 py-0.5">
                  {s.replace("_", " ")}
                </span>
              ))}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
