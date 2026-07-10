"use client";

import { use, useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Clock, IndianRupee, LayoutGrid } from "lucide-react";
import { getVenue, listCourts } from "@/lib/api/venues";
import { queryKeys } from "@/lib/queryKeys";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Skeleton, SkeletonCard } from "@/components/ui/Skeleton";
import { getSportTheme, sportLabel } from "@/lib/sportTheme";

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
        {venue ? <h1 className="text-xl font-bold">{venue.name}</h1> : <Skeleton className="h-6 w-40" />}
        <p className="text-ink-muted text-sm mt-1">{venue?.city}</p>
      </div>

      {venue && (
        <div className="flex flex-wrap gap-2">
          {venue.sports.map((s) => {
            const theme = getSportTheme(s);
            const active = sportFilter === s;
            return (
              <button
                key={s}
                onClick={() => setSportFilter(active ? null : s)}
                className={`rounded-full px-3 py-1.5 text-xs font-semibold capitalize transition-colors ${
                  active ? `${theme.solid} text-white` : theme.light
                }`}
              >
                {sportLabel(s)}
              </button>
            );
          })}
        </div>
      )}

      {isLoading && (
        <div className="space-y-3">
          <SkeletonCard />
          <SkeletonCard />
        </div>
      )}

      <div className="space-y-3">
        {visibleCourts?.map((court) => {
          const theme = getSportTheme(court.sport);
          const Icon = theme.icon;
          return (
            <Link key={court.court_id} href={`/venues/${tenantId}/courts/${court.court_id}/book`}>
              <Card accentGradient={theme.gradient} interactive>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className={`flex h-10 w-10 items-center justify-center rounded-xl ${theme.light}`}>
                      <Icon size={18} strokeWidth={2.25} />
                    </span>
                    <div>
                      <p className="font-semibold">{court.name}</p>
                      <p className="text-sm text-ink-muted capitalize">{sportLabel(court.sport)}</p>
                      <p className="text-xs text-ink-muted flex items-center gap-1 mt-0.5">
                        <Clock size={12} /> {court.open_time} – {court.close_time}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-bold flex items-center gap-0.5 justify-end">
                      <IndianRupee size={14} />
                      {court.hourly_price}
                    </p>
                    <p className="text-xs text-ink-muted">per hour</p>
                  </div>
                </div>
              </Card>
            </Link>
          );
        })}
        {visibleCourts && visibleCourts.length === 0 && (
          <EmptyState icon={LayoutGrid} title="No courts for this filter" description="Try a different sport." />
        )}
      </div>
    </div>
  );
}
