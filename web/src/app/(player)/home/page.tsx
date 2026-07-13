"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Calendar, Clock, Compass, Flame, Trophy, Wallet as WalletIcon } from "lucide-react";
import { useSession } from "@/components/providers/SessionProvider";
import { getPlayerEngagement } from "@/lib/api/kpis";
import { listMyBookings } from "@/lib/api/bookings";
import { queryKeys } from "@/lib/queryKeys";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { StatTile } from "@/components/ui/StatTile";
import { FootballSpinner } from "@/components/ui/FootballSpinner";
import { getSportTheme, sportLabel } from "@/lib/sportTheme";

const QUICK_ACTIONS = [
  { href: "/venues", label: "Book a court", icon: Compass },
  { href: "/bookings", label: "My bookings", icon: Calendar },
  { href: "/wallet", label: "Wallet", icon: WalletIcon },
];

export default function HomePage() {
  const session = useSession();
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: queryKeys.engagement(session.uid),
    queryFn: () => getPlayerEngagement(session.uid, "month"),
  });
  const { data: bookings, isLoading: bookingsLoading } = useQuery({
    queryKey: queryKeys.myBookings(),
    queryFn: listMyBookings,
  });

  const upcoming = bookings
    ?.filter((b) => b.status === "confirmed")
    .sort((a, b) => (a.date < b.date ? -1 : 1))
    .slice(0, 3);

  return (
    <div className="space-y-6">
      <div className="rounded-3xl bg-gradient-to-br from-brand-from to-brand-to p-5 text-white shadow-lg shadow-indigo-600/20">
        <h1 className="text-xl font-bold">
          Hey {session.display_name?.split(" ")[0] || "there"} 👋
        </h1>
        <p className="text-white/80 text-sm mt-0.5">What do you want to play today?</p>
      </div>

      <div className="grid grid-cols-3 gap-3">
        {QUICK_ACTIONS.map((action) => {
          const Icon = action.icon;
          return (
            <Link
              key={action.href}
              href={action.href}
              className="flex flex-col items-center justify-center gap-1.5 rounded-2xl border border-border bg-surface p-4 text-center shadow-sm transition-shadow hover:shadow-md"
            >
              <span className="flex h-10 w-10 items-center justify-center rounded-full bg-indigo-50 text-indigo-600">
                <Icon size={18} strokeWidth={2.25} />
              </span>
              <span className="text-xs font-medium text-foreground">{action.label}</span>
            </Link>
          );
        })}
      </div>

      {statsLoading ? (
        <FootballSpinner />
      ) : (
        stats && (
          <Card>
            <p className="text-sm font-semibold mb-3">This month</p>
            <div className="grid grid-cols-3 gap-3">
              <StatTile icon={Trophy} label="Matches" value={stats.matches_played} accent="bg-indigo-50 text-indigo-600" />
              <StatTile icon={Clock} label="Hours played" value={stats.hours_played} accent="bg-teal-50 text-teal-600" />
              <StatTile icon={WalletIcon} label="Wallet" value={`₹${stats.wallet_balance}`} accent="bg-amber-50 text-amber-600" />
            </div>
            {stats.favorite_sport && (
              <p className="text-xs text-ink-muted mt-3 text-center">
                Favorite sport:{" "}
                <span className="font-medium text-foreground">{sportLabel(stats.favorite_sport)}</span>
              </p>
            )}
          </Card>
        )
      )}

      <div>
        <div className="flex items-center justify-between mb-2">
          <p className="text-sm font-semibold">Upcoming bookings</p>
          {upcoming && upcoming.length > 0 && (
            <Link href="/bookings" className="text-xs font-medium text-indigo-600">
              See all
            </Link>
          )}
        </div>
        {bookingsLoading && <FootballSpinner />}
        {upcoming && upcoming.length === 0 && (
          <Card className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-indigo-50 text-indigo-600">
              <Flame size={16} strokeWidth={2.25} />
            </span>
            <div>
              <p className="text-sm font-medium">No upcoming bookings yet</p>
              <p className="text-xs text-ink-muted">Explore venues to book your next match.</p>
            </div>
          </Card>
        )}
        <div className="space-y-2">
          {upcoming?.map((b) => {
            const theme = getSportTheme(b.sport);
            return (
              <Link key={b.booking_id} href={`/bookings/${b.booking_id}`}>
                <Card accentGradient={theme.gradient} interactive>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-semibold">{sportLabel(b.sport)}</p>
                      <p className="text-xs text-ink-muted">
                        {b.date} · {b.start_time}–{b.end_time}
                        {b.team_name ? ` · ${b.team_name}` : ""}
                      </p>
                    </div>
                    <Badge status={b.status}>{b.status.replace("_", " ")}</Badge>
                  </div>
                </Card>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}
