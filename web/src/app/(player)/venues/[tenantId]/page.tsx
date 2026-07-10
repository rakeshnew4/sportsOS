"use client";

import { use, useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { getVenue, listCourts } from "@/lib/api/venues";
import { queryKeys } from "@/lib/queryKeys";

export default function VenueDetailPage({ params }: { params: Promise<{ tenantId: string }> }) {
  const { tenantId } = use(params);
  const [sportFilter, setSportFilter] = useState<string | null>(null);

  const { data: venue } = useQuery({
    queryKey: queryKeys.venue(tenantId),
    queryFn: () => getVenue(tenantId),
  });
  const { data: courts, isLoading } = useQuery({
    queryKey: queryKeys.courts(tenantId),
    queryFn: () => listCourts(tenantId),
  });

  const visibleCourts = courts?.filter((c) => !sportFilter || c.sport === sportFilter);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold">{venue?.name || "Loading…"}</h1>
        <p className="text-neutral-500 text-sm">{venue?.city}</p>
      </div>

      {venue && (
        <div className="flex flex-wrap gap-2">
          {venue.sports.map((s) => (
            <button
              key={s}
              onClick={() => setSportFilter(sportFilter === s ? null : s)}
              className={`rounded-full px-3 py-1.5 text-xs font-medium border transition-colors ${
                sportFilter === s
                  ? "bg-emerald-600 text-white border-emerald-600"
                  : "bg-white text-neutral-600 border-neutral-300"
              }`}
            >
              {s.replace("_", " ")}
            </button>
          ))}
        </div>
      )}

      {isLoading && <p className="text-sm text-neutral-500">Loading courts…</p>}

      <div className="space-y-3">
        {visibleCourts?.map((court) => (
          <Link
            key={court.court_id}
            href={`/venues/${tenantId}/courts/${court.court_id}/book`}
            className="flex items-center justify-between rounded-2xl border border-neutral-200 bg-white p-4 shadow-sm hover:shadow-md transition-shadow"
          >
            <div>
              <p className="font-semibold text-neutral-900">{court.name}</p>
              <p className="text-sm text-neutral-500">{court.sport.replace("_", " ")}</p>
              <p className="text-xs text-neutral-400">
                {court.open_time} – {court.close_time}
              </p>
            </div>
            <div className="text-right">
              <p className="font-semibold text-neutral-900">₹{court.hourly_price}</p>
              <p className="text-xs text-neutral-400">per hour</p>
            </div>
          </Link>
        ))}
        {visibleCourts && visibleCourts.length === 0 && (
          <p className="text-sm text-neutral-500">No courts for this filter.</p>
        )}
      </div>
    </div>
  );
}
