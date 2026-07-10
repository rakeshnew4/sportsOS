"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useSession } from "@/components/providers/SessionProvider";
import { getPlayerEngagement } from "@/lib/api/kpis";
import { queryKeys } from "@/lib/queryKeys";

const QUICK_ACTIONS = [
  { href: "/venues", label: "Book a court", icon: "🏸", color: "bg-emerald-50 text-emerald-700" },
  { href: "/bookings", label: "My bookings", icon: "📅", color: "bg-blue-50 text-blue-700" },
  { href: "/wallet", label: "Wallet", icon: "💰", color: "bg-amber-50 text-amber-700" },
];

export default function HomePage() {
  const session = useSession();
  const { data: stats } = useQuery({
    queryKey: queryKeys.engagement(session.uid),
    queryFn: () => getPlayerEngagement(session.uid, "month"),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold">Hey {session.display_name?.split(" ")[0] || "there"} 👋</h1>
        <p className="text-neutral-500 text-sm">What do you want to play today?</p>
      </div>

      <div className="grid grid-cols-3 gap-3">
        {QUICK_ACTIONS.map((action) => (
          <Link
            key={action.href}
            href={action.href}
            className="flex flex-col items-center justify-center gap-1.5 rounded-2xl border border-neutral-200 bg-white p-4 text-center shadow-sm hover:shadow-md transition-shadow"
          >
            <span className={`flex h-10 w-10 items-center justify-center rounded-full text-lg ${action.color}`}>
              {action.icon}
            </span>
            <span className="text-xs font-medium text-neutral-700">{action.label}</span>
          </Link>
        ))}
      </div>

      {stats && (
        <div className="rounded-2xl border border-neutral-200 bg-white p-4">
          <p className="text-sm font-semibold text-neutral-700 mb-3">This month</p>
          <div className="grid grid-cols-3 gap-3 text-center">
            <div>
              <p className="text-lg font-bold">{stats.matches_played}</p>
              <p className="text-xs text-neutral-500">Matches</p>
            </div>
            <div>
              <p className="text-lg font-bold">{stats.hours_played}</p>
              <p className="text-xs text-neutral-500">Hours played</p>
            </div>
            <div>
              <p className="text-lg font-bold">₹{stats.wallet_balance}</p>
              <p className="text-xs text-neutral-500">Wallet</p>
            </div>
          </div>
          {stats.favorite_sport && (
            <p className="text-xs text-neutral-500 mt-3 text-center">
              Favorite sport: <span className="font-medium text-neutral-700">{stats.favorite_sport}</span>
            </p>
          )}
        </div>
      )}
    </div>
  );
}
