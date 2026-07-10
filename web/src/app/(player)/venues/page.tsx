"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { MapPin, Search } from "lucide-react";
import { listVenues } from "@/lib/api/venues";
import { queryKeys } from "@/lib/queryKeys";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { SkeletonCard } from "@/components/ui/Skeleton";
import { getSportTheme, sportLabel } from "@/lib/sportTheme";

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
        <p className="text-ink-muted text-sm">Pick a sport and city to see what's nearby.</p>
      </div>

      <div className="relative">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted" />
        <input
          type="text"
          placeholder="City"
          value={city}
          onChange={(e) => setCity(e.target.value)}
          className="w-full rounded-xl border border-border bg-surface py-2.5 pl-9 pr-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      <div className="flex flex-wrap gap-2">
        {SPORTS.map((s) => {
          const theme = getSportTheme(s);
          const active = sport === s;
          return (
            <button
              key={s}
              onClick={() => setSport(active ? null : s)}
              className={`rounded-full px-3 py-1.5 text-xs font-semibold capitalize transition-colors ${
                active ? `${theme.solid} text-white` : `${theme.light}`
              }`}
            >
              {sportLabel(s)}
            </button>
          );
        })}
      </div>

      {isLoading && (
        <div className="space-y-3">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
      )}
      {venues && venues.length === 0 && (
        <EmptyState icon={MapPin} title="No venues match those filters" description="Try a different sport or city." />
      )}

      <div className="space-y-3">
        {venues?.map((venue) => (
          <Link key={venue.tenant_id} href={`/venues/${venue.tenant_id}`}>
            <Card interactive>
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-semibold">{venue.name}</p>
                  <p className="text-sm text-ink-muted flex items-center gap-1 mt-0.5">
                    <MapPin size={13} /> {venue.city}
                  </p>
                </div>
              </div>
              <div className="flex flex-wrap gap-1.5 mt-3">
                {venue.sports.map((s) => {
                  const theme = getSportTheme(s);
                  return (
                    <span key={s} className={`text-xs font-medium rounded-full px-2 py-0.5 ${theme.light}`}>
                      {sportLabel(s)}
                    </span>
                  );
                })}
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
