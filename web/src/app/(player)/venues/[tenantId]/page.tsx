"use client";

import { use, useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Clock, IndianRupee, LayoutGrid, MapPin, Star } from "lucide-react";
import { getVenue, listCourts } from "@/lib/api/venues";
import { getVenueRatingsStats } from "@/lib/api/ratings";
import { queryKeys } from "@/lib/queryKeys";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { FootballSpinner } from "@/components/ui/FootballSpinner";
import { SportFilterChips } from "@/components/ui/SportFilterChips";
import { getSportFallbackImage, getSportTheme, sportLabel } from "@/lib/sportTheme";

export default function VenueDetailPage({ params }: { params: Promise<{ tenantId: string }> }) {
  const { tenantId } = use(params);
  const [sportFilter, setSportFilter] = useState("");

  const { data: venue } = useQuery({
    queryKey: queryKeys.venue(tenantId),
    queryFn: () => getVenue(tenantId),
  });
  const { data: courts, isLoading } = useQuery({
    queryKey: queryKeys.courts(tenantId),
    queryFn: () => listCourts(tenantId),
  });
  const { data: ratings } = useQuery({
    queryKey: queryKeys.venueRatingsStats(tenantId),
    queryFn: () => getVenueRatingsStats(tenantId),
  });

  const visibleCourts = courts?.filter((c) => !sportFilter || c.sport === sportFilter);
  const primaryTheme = getSportTheme(venue?.sports[0]);
  const bgImage = venue
    ? venue.cover_image_url || getSportFallbackImage(venue.sports[0]) || "/brand/venues-arena.jpg"
    : null;

  return (
    <div className="space-y-4">
      {venue ? (
        <div
          className={`rounded-3xl overflow-hidden ${bgImage ? "" : `bg-gradient-to-br ${primaryTheme.gradient}`}`}
          style={bgImage ? { backgroundImage: `url(${bgImage})`, backgroundSize: "cover", backgroundPosition: "center" } : undefined}
        >
          <div className={`p-5 ${bgImage ? "bg-black/35 backdrop-blur-[1px]" : ""}`}>
            <h1 className="text-xl font-bold text-white">{venue.name}</h1>
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1 text-sm text-white/85">
              <span className="flex items-center gap-1">
                <MapPin size={13} /> {venue.address ? `${venue.address}, ${venue.city}` : venue.city}
              </span>
              {ratings && ratings.total_ratings > 0 && (
                <span className="flex items-center gap-1">
                  <Star size={13} strokeWidth={2.5} className="fill-amber-400 text-amber-400" />
                  {ratings.avg_rating} ({ratings.total_ratings})
                </span>
              )}
            </div>
          </div>
        </div>
      ) : (
        <FootballSpinner />
      )}

      {venue?.description && <p className="text-sm text-ink-muted">{venue.description}</p>}

      {venue && venue.amenities.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {venue.amenities.map((a) => (
            <span key={a} className="rounded-full bg-surface-muted px-2.5 py-1 text-xs font-medium text-ink-muted">
              {a}
            </span>
          ))}
        </div>
      )}

      {venue && <SportFilterChips value={sportFilter} onChange={setSportFilter} sports={venue.sports} />}

      {isLoading && <FootballSpinner />}

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
