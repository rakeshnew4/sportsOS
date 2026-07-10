"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useSession } from "@/components/providers/SessionProvider";
import { listNotifications } from "@/lib/api/notifications";
import { queryKeys } from "@/lib/queryKeys";

const NAV_ITEMS = [
  { href: "/", label: "Home", icon: "🏠" },
  { href: "/venues", label: "Venues", icon: "🔍" },
  { href: "/play", label: "Play", icon: "⚡" },
  { href: "/teams", label: "Teams", icon: "🤝" },
  { href: "/bookings", label: "Bookings", icon: "📅" },
  { href: "/rewards", label: "Rewards", icon: "🏆" },
  { href: "/wallet", label: "Wallet", icon: "💰" },
  { href: "/notifications", label: "Alerts", icon: "🔔" },
];

export function PlayerNav() {
  const pathname = usePathname();
  const router = useRouter();
  const session = useSession();

  const { data: unread } = useQuery({
    queryKey: queryKeys.notifications(true),
    queryFn: () => listNotifications({ unreadOnly: true, limit: 50 }),
    refetchInterval: 60_000,
  });
  const unreadCount = unread?.length ?? 0;

  async function handleLogout() {
    await fetch("/api/auth/logout", { method: "POST" });
    router.push("/login");
    router.refresh();
  }

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden md:flex md:w-56 md:flex-col md:border-r md:border-neutral-200 md:bg-white md:p-4">
        <div className="mb-6 px-2">
          <p className="font-bold text-lg">🏟️ SportsOS</p>
          <p className="text-sm text-neutral-500 truncate">{session.display_name}</p>
        </div>
        <nav className="flex-1 space-y-1">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                pathname === item.href
                  ? "bg-emerald-50 text-emerald-700"
                  : "text-neutral-600 hover:bg-neutral-100"
              }`}
            >
              <span>{item.icon}</span>
              {item.label}
              {item.href === "/notifications" && unreadCount > 0 && (
                <span className="ml-auto rounded-full bg-red-500 text-white text-xs px-1.5">
                  {unreadCount}
                </span>
              )}
            </Link>
          ))}
        </nav>
        <Link
          href="/admin"
          className="text-left text-sm text-neutral-500 hover:text-neutral-800 px-3 py-2"
        >
          🏟️ Manage venues
        </Link>
        <button
          onClick={handleLogout}
          className="mt-2 text-left text-sm text-neutral-500 hover:text-neutral-800 px-3 py-2"
        >
          Log out
        </button>
      </aside>

      {/* Mobile bottom nav */}
      <nav className="fixed bottom-0 left-0 right-0 z-10 flex md:hidden border-t border-neutral-200 bg-white">
        {NAV_ITEMS.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`flex-1 flex flex-col items-center gap-0.5 py-2.5 text-xs font-medium ${
              pathname === item.href ? "text-emerald-700" : "text-neutral-500"
            }`}
          >
            <span className="relative text-lg">
              {item.icon}
              {item.href === "/notifications" && unreadCount > 0 && (
                <span className="absolute -top-1 -right-2 rounded-full bg-red-500 text-white text-[10px] px-1">
                  {unreadCount}
                </span>
              )}
            </span>
            {item.label}
          </Link>
        ))}
      </nav>
    </>
  );
}
