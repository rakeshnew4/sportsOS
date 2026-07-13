"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ChevronRight, MapPin, Search } from "lucide-react";
import { listVenues } from "@/lib/api/venues";
import { queryKeys } from "@/lib/queryKeys";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { FootballSpinner } from "@/components/ui/FootballSpinner";
import { SportFilterChips } from "@/components/ui/SportFilterChips";
import { getSportFallbackImage, getSportTheme, sportLabel } from "@/lib/sportTheme";

export default function VenuesPage() {
  const [sport, setSport] = useState("");
  const [city, setCity] = useState("");

  const { data: venues, isLoading } = useQuery({
    queryKey: queryKeys.venues({ city: city || undefined, sport: sport || undefined }),
    queryFn: () => listVenues({ city: city || undefined, sport: sport || undefined }),
  });

  return (
    <div className="space-y-4">
      <div className="relative overflow-hidden rounded-3xl h-36 sm:h-44">
        <Image
          src="/brand/venues-arena.jpg"
          alt=""
          fill
          priority
          sizes="(min-width: 1280px) 1152px, 100vw"
          className="object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/75 via-black/25 to-black/10" />
        <div className="absolute inset-0 flex flex-col justify-end p-5">
          <h1 className="text-xl font-bold text-white">Find a venue</h1>
          <p className="text-white/85 text-sm mt-0.5">
            {venues ? `${venues.length} venue${venues.length === 1 ? "" : "s"} found` : "Pick a sport and city to see what's nearby."}
          </p>
        </div>
      </div>

      <div className="relative">
        <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-ink-muted" />
        <input
          type="text"
          placeholder="City"
          value={city}
          onChange={(e) => setCity(e.target.value)}
          className="w-full rounded-full border border-border bg-surface py-2.5 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      <SportFilterChips value={sport} onChange={setSport} />

      {isLoading && <FootballSpinner />}
      {venues && venues.length === 0 && (
        <EmptyState icon={MapPin} title="No venues match those filters" description="Try a different sport or city." />
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-3">
        {venues?.map((venue) => {
          const primaryTheme = getSportTheme(venue.sports[0]);
          const bgImage = venue.cover_image_url || getSportFallbackImage(venue.sports[0]) || "/brand/venues-arena.jpg";
          return (
            <Link key={venue.tenant_id} href={`/venues/${venue.tenant_id}`}>
              <Card interactive className="overflow-hidden !p-0">
                <div
                  className={`h-16 flex items-center px-4 ${
                    bgImage ? "bg-cover bg-center" : `bg-gradient-to-r ${primaryTheme.gradient}`
                  }`}
                  style={bgImage ? { backgroundImage: `url(${bgImage})` } : undefined}
                >
                  <span className="flex h-9 w-9 items-center justify-center rounded-full bg-white/20 text-white backdrop-blur-sm">
                    <primaryTheme.icon size={17} strokeWidth={2.25} />
                  </span>
                </div>
                <div className="p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="font-semibold truncate">{venue.name}</p>
                      <p className="text-sm text-ink-muted flex items-center gap-1 mt-0.5">
                        <MapPin size={13} /> {venue.city}
                      </p>
                    </div>
                    <ChevronRight size={18} className="text-ink-muted shrink-0 mt-1" />
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
                </div>
              </Card>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
