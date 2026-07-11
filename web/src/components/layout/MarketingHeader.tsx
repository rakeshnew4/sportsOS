"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Calendar, Trophy, Zap } from "lucide-react";
import { Button } from "@/components/ui/Button";

const NAV_TABS = [
  { href: "/login", label: "Play", icon: Zap },
  { href: "/login", label: "Book", icon: Calendar },
  { href: "/login", label: "Rewards", icon: Trophy },
];

export function MarketingHeader() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-10 bg-surface/95 backdrop-blur border-b border-border">
      <nav className="flex items-center justify-between gap-4 px-4 py-3 md:px-8 max-w-6xl mx-auto">
        <Link href="/" className="flex items-center gap-2 shrink-0">
          <Image src="/brand/logo-mark.png" alt="" width={32} height={32} className="h-8 w-8" priority />
          <span className="font-bold text-sm">SportsOS</span>
        </Link>

        <div className="hidden md:flex items-center gap-8">
          {NAV_TABS.map((tab) => {
            const Icon = tab.icon;
            return (
              <Link
                key={tab.label}
                href={tab.href}
                className="flex items-center gap-1.5 text-sm font-medium text-ink-muted hover:text-foreground transition-colors"
              >
                <Icon size={16} strokeWidth={2.25} />
                {tab.label}
              </Link>
            );
          })}
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <Link
            href="/login"
            className={`hidden sm:inline text-sm font-semibold px-4 py-2.5 rounded-full transition-colors ${
              pathname === "/login" ? "text-foreground" : "text-ink-muted hover:text-foreground"
            }`}
          >
            Log in
          </Link>
          <Link href="/signup">
            <Button variant="gradient" pill className="text-sm px-5">
              Get started
            </Button>
          </Link>
        </div>
      </nav>
    </header>
  );
}
