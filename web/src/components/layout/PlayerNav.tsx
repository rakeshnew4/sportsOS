"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  Bell,
  Calendar,
  Compass,
  Home as HomeIcon,
  LogOut,
  MoreHorizontal,
  ShieldCheck,
  Trophy,
  Users,
  Wallet as WalletIcon,
  X,
  Zap,
} from "lucide-react";
import { useSession } from "@/components/providers/SessionProvider";
import { listNotifications } from "@/lib/api/notifications";
import { queryKeys } from "@/lib/queryKeys";

const NAV_ITEMS = [
  { href: "/", label: "Home", icon: HomeIcon },
  { href: "/venues", label: "Venues", icon: Compass },
  { href: "/play", label: "Play", icon: Zap },
  { href: "/teams", label: "Teams", icon: Users },
  { href: "/bookings", label: "Bookings", icon: Calendar },
  { href: "/rewards", label: "Rewards", icon: Trophy },
  { href: "/wallet", label: "Wallet", icon: WalletIcon },
  { href: "/notifications", label: "Alerts", icon: Bell },
];

const MOBILE_PRIMARY = ["/", "/play", "/bookings", "/wallet"];

export function PlayerNav() {
  const pathname = usePathname();
  const router = useRouter();
  const session = useSession();
  const [moreOpen, setMoreOpen] = useState(false);

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

  const primaryItems = NAV_ITEMS.filter((i) => MOBILE_PRIMARY.includes(i.href));
  const moreItems = NAV_ITEMS.filter((i) => !MOBILE_PRIMARY.includes(i.href));

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden md:flex md:w-60 md:flex-col md:border-r md:border-border md:bg-surface md:p-4">
        <div className="mb-6 flex items-center gap-2.5 px-2">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-brand-from to-brand-to text-white font-bold text-sm shadow-md shadow-indigo-600/20">
            {(session.display_name || "S").charAt(0).toUpperCase()}
          </span>
          <div className="min-w-0">
            <p className="font-bold text-sm leading-tight">SportsOS</p>
            <p className="text-xs text-ink-muted truncate">{session.display_name}</p>
          </div>
        </div>
        <nav className="flex-1 space-y-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-2.5 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${
                  active
                    ? "bg-gradient-to-r from-brand-from to-brand-to text-white shadow-md shadow-indigo-600/20"
                    : "text-ink-muted hover:bg-surface-muted hover:text-foreground"
                }`}
              >
                <Icon size={17} strokeWidth={2.25} />
                {item.label}
                {item.href === "/notifications" && unreadCount > 0 && (
                  <span
                    className={`ml-auto flex h-5 min-w-5 items-center justify-center rounded-full px-1 text-[11px] font-bold ${
                      active ? "bg-white/25 text-white" : "bg-red-500 text-white"
                    }`}
                  >
                    {unreadCount}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>
        <Link
          href="/admin"
          className="flex items-center gap-2.5 rounded-xl px-3 py-2.5 text-sm font-medium text-ink-muted hover:bg-surface-muted hover:text-foreground"
        >
          <ShieldCheck size={17} strokeWidth={2.25} />
          Manage venues
        </Link>
        <button
          onClick={handleLogout}
          className="mt-1 flex items-center gap-2.5 rounded-xl px-3 py-2.5 text-left text-sm font-medium text-ink-muted hover:bg-surface-muted hover:text-foreground"
        >
          <LogOut size={17} strokeWidth={2.25} />
          Log out
        </button>
      </aside>

      {/* Mobile bottom nav */}
      <nav className="fixed bottom-0 left-0 right-0 z-10 flex md:hidden border-t border-border bg-surface/95 backdrop-blur">
        {primaryItems.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className="flex-1 flex flex-col items-center gap-0.5 py-2.5 text-[11px] font-semibold"
            >
              <span
                className={`flex h-8 w-8 items-center justify-center rounded-full ${
                  active ? "bg-gradient-to-br from-brand-from to-brand-to text-white shadow-md shadow-indigo-600/25" : "text-ink-muted"
                }`}
              >
                <Icon size={17} strokeWidth={2.25} />
              </span>
              <span className={active ? "text-foreground" : "text-ink-muted"}>{item.label}</span>
            </Link>
          );
        })}
        <button
          onClick={() => setMoreOpen(true)}
          className="flex-1 flex flex-col items-center gap-0.5 py-2.5 text-[11px] font-semibold text-ink-muted"
        >
          <span className="relative flex h-8 w-8 items-center justify-center rounded-full">
            <MoreHorizontal size={17} strokeWidth={2.25} />
            {unreadCount > 0 && (
              <span className="absolute -top-0.5 right-0.5 h-2 w-2 rounded-full bg-red-500" />
            )}
          </span>
          More
        </button>
      </nav>

      {moreOpen && (
        <div className="fixed inset-0 z-30 md:hidden">
          <button
            aria-label="Close menu"
            onClick={() => setMoreOpen(false)}
            className="absolute inset-0 bg-black/40"
          />
          <div className="absolute bottom-0 left-0 right-0 rounded-t-3xl bg-surface p-4 pb-6 shadow-[0_-8px_24px_rgba(0,0,0,0.15)]">
            <div className="mx-auto mb-3 h-1 w-10 rounded-full bg-black/10" />
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm font-semibold">More</p>
              <button onClick={() => setMoreOpen(false)} className="text-ink-muted">
                <X size={18} />
              </button>
            </div>
            <div className="grid grid-cols-3 gap-3">
              {moreItems.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMoreOpen(false)}
                    className="flex flex-col items-center gap-1.5 rounded-2xl border border-border bg-surface-muted/60 py-3 text-xs font-medium text-foreground"
                  >
                    <span className="relative flex h-9 w-9 items-center justify-center rounded-full bg-surface shadow-sm">
                      <Icon size={17} strokeWidth={2.25} />
                      {item.href === "/notifications" && unreadCount > 0 && (
                        <span className="absolute -top-1 -right-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white">
                          {unreadCount}
                        </span>
                      )}
                    </span>
                    {item.label}
                  </Link>
                );
              })}
              <Link
                href="/admin"
                onClick={() => setMoreOpen(false)}
                className="flex flex-col items-center gap-1.5 rounded-2xl border border-border bg-surface-muted/60 py-3 text-xs font-medium text-foreground"
              >
                <span className="flex h-9 w-9 items-center justify-center rounded-full bg-surface shadow-sm">
                  <ShieldCheck size={17} strokeWidth={2.25} />
                </span>
                Manage venues
              </Link>
              <button
                onClick={handleLogout}
                className="flex flex-col items-center gap-1.5 rounded-2xl border border-border bg-surface-muted/60 py-3 text-xs font-medium text-red-600"
              >
                <span className="flex h-9 w-9 items-center justify-center rounded-full bg-surface shadow-sm">
                  <LogOut size={17} strokeWidth={2.25} />
                </span>
                Log out
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
