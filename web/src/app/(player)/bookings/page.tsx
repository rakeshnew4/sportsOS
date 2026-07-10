"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { CalendarX2, IndianRupee } from "lucide-react";
import { listMyBookings } from "@/lib/api/bookings";
import { queryKeys } from "@/lib/queryKeys";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import { SkeletonCard } from "@/components/ui/Skeleton";
import { getSportTheme, sportLabel } from "@/lib/sportTheme";

export default function BookingsPage() {
  const { data: bookings, isLoading } = useQuery({
    queryKey: queryKeys.myBookings(),
    queryFn: listMyBookings,
  });

  const sorted = bookings?.slice().sort((a, b) => (a.date < b.date ? 1 : -1));

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold">My bookings</h1>
        <p className="text-ink-muted text-sm">Courts you've booked.</p>
      </div>

      {isLoading && (
        <div className="space-y-3">
          <SkeletonCard />
          <SkeletonCard />
        </div>
      )}
      {sorted && sorted.length === 0 && (
        <EmptyState icon={CalendarX2} title="No bookings yet" description="Go book a court to get started." />
      )}

      <div className="space-y-3">
        {sorted?.map((booking) => {
          const theme = getSportTheme(booking.sport);
          return (
            <Link key={booking.booking_id} href={`/bookings/${booking.booking_id}`}>
              <Card accentGradient={theme.gradient} interactive>
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-semibold">{sportLabel(booking.sport)}</p>
                    <p className="text-sm text-ink-muted">
                      {booking.date} · {booking.start_time} – {booking.end_time}
                    </p>
                    {booking.team_name && (
                      <p className="text-xs text-ink-muted mt-1">{booking.team_name}</p>
                    )}
                  </div>
                  <Badge status={booking.status}>{booking.status.replace("_", " ")}</Badge>
                </div>
                <p className="text-sm font-semibold mt-2 flex items-center gap-0.5">
                  <IndianRupee size={13} />
                  {booking.price}
                </p>
              </Card>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
