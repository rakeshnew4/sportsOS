"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/admin/superadmin", label: "Admin accounts" },
  { href: "/admin/superadmin/broadcast", label: "Broadcast" },
];

export function SuperadminNav() {
  const pathname = usePathname();

  return (
    <nav className="flex gap-1 overflow-x-auto rounded-xl bg-neutral-100 p-1 mb-4">
      {NAV_ITEMS.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          className={`flex items-center gap-1.5 whitespace-nowrap rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
            pathname === item.href ? "bg-white shadow-sm text-neutral-900" : "text-neutral-500"
          }`}
        >
          {item.label}
        </Link>
      ))}
    </nav>
  );
}
