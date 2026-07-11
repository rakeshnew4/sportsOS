import Image from "next/image";
import Link from "next/link";

const PRODUCT_LINKS = [
  { href: "/login", label: "Play" },
  { href: "/login", label: "Book a venue" },
  { href: "/login", label: "Teams" },
  { href: "/login", label: "Rewards" },
];

export function MarketingFooter() {
  return (
    <footer className="border-t border-border bg-surface mt-16">
      <div className="max-w-6xl mx-auto px-4 md:px-8 py-10 grid gap-8 sm:grid-cols-2 md:grid-cols-4">
        <div className="sm:col-span-2 md:col-span-1">
          <div className="flex items-center gap-2 mb-2">
            <Image src="/brand/logo-mark.png" alt="" width={28} height={28} className="h-7 w-7" />
            <span className="font-bold text-sm">SportsOS</span>
          </div>
          <p className="text-sm text-ink-muted">Book a court. Join a match. Play.</p>
        </div>

        <div>
          <p className="text-xs font-semibold text-ink-muted uppercase tracking-wide mb-3">Product</p>
          <ul className="space-y-2">
            {PRODUCT_LINKS.map((link) => (
              <li key={link.label}>
                <Link href={link.href} className="text-sm text-foreground hover:text-brand-from">
                  {link.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <p className="text-xs font-semibold text-ink-muted uppercase tracking-wide mb-3">Account</p>
          <ul className="space-y-2">
            <li>
              <Link href="/login" className="text-sm text-foreground hover:text-brand-from">
                Log in
              </Link>
            </li>
            <li>
              <Link href="/signup" className="text-sm text-foreground hover:text-brand-from">
                Sign up
              </Link>
            </li>
          </ul>
        </div>

        <div>
          <p className="text-xs font-semibold text-ink-muted uppercase tracking-wide mb-3">For venues</p>
          <ul className="space-y-2">
            <li>
              <Link href="/signup" className="text-sm text-foreground hover:text-brand-from">
                List your venue
              </Link>
            </li>
          </ul>
        </div>
      </div>

      <div className="border-t border-border">
        <p className="max-w-6xl mx-auto px-4 md:px-8 py-4 text-xs text-ink-muted">
          © {new Date().getFullYear()} SportsOS. All rights reserved.
        </p>
      </div>
    </footer>
  );
}
