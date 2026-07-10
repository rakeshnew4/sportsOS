"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export function AdminNav({ tenantId }: { tenantId: string }) {
  const pathname = usePathname();
  const base = `/admin/${tenantId}`;
  const NAV_ITEMS = [
    { href: base, label: "Overview", icon: "📊" },
    { href: `${base}/bookings`, label: "Bookings", icon: "📅" },
    { href: `${base}/courts`, label: "Courts", icon: "🏸" },
    { href: `${base}/staff`, label: "Staff", icon: "👥" },
  ];

  return (
    <>
      <nav className="flex gap-1 overflow-x-auto rounded-xl bg-neutral-100 p-1 mb-4">
        {NAV_ITEMS.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`flex items-center gap-1.5 whitespace-nowrap rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
              pathname === item.href ? "bg-white shadow-sm text-neutral-900" : "text-neutral-500"
            }`}
          >
            <span>{item.icon}</span>
            {item.label}
          </Link>
        ))}
      </nav>
      <Link href="/admin" className="text-xs text-neutral-400 hover:text-neutral-600 mb-4 inline-block">
        ← All venues
      </Link>
    </>
  );
}
