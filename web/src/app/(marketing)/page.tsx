import Image from "next/image";
import Link from "next/link";
import { ArrowRight, Building2, CalendarCheck, Trophy, Users2 } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ALL_SPORTS, getSportTheme, sportLabel } from "@/lib/sportTheme";

const VALUE_PROPS = [
  {
    icon: CalendarCheck,
    title: "Book instantly",
    description: "Real-time slot availability and pricing — no back-and-forth, no waiting to hear back.",
  },
  {
    icon: Users2,
    title: "Play with the community",
    description: "Join an open match or queue up with others until you've got enough players for a game.",
  },
  {
    icon: Trophy,
    title: "Earn rewards",
    description: "Rack up points, climb the leaderboard, and refer friends for extra perks.",
  },
];

export default function MarketingHomePage() {
  return (
    <div className="max-w-6xl mx-auto px-4 md:px-8">
      {/* Hero */}
      <section className="pt-10 md:pt-16 pb-12">
        <div className="relative overflow-hidden rounded-[2.5rem] p-8 md:p-16 text-center">
          <Image
            src="/brand/hero-stadium.jpg"
            alt=""
            fill
            priority
            sizes="(min-width: 1280px) 1152px, 100vw"
            className="object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-b from-black/75 via-black/60 to-black/80" />
          <div className="relative">
            <h1 className="text-3xl md:text-5xl font-bold tracking-tight text-white max-w-3xl mx-auto text-balance">
              Book courts, join matches, and play more — near you.
            </h1>
            <p className="text-white/85 text-base md:text-lg mt-4 max-w-xl mx-auto">
              SportsOS brings venue booking, open games, and a community of players together in one place.
            </p>
            <div className="flex flex-wrap items-center justify-center gap-3 mt-8">
              <Link href="/signup">
                <Button variant="gradient" pill className="px-7 py-3 text-base">
                  Get started
                </Button>
              </Link>
              <Link href="/login">
                <Button variant="secondary" pill className="px-7 py-3 text-base">
                  Log in
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Popular sports */}
      <section className="py-8">
        <h2 className="text-lg font-bold mb-4">Popular sports</h2>
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-3">
          {ALL_SPORTS.map((sport) => {
            const theme = getSportTheme(sport);
            const Icon = theme.icon;
            return (
              <Link
                key={sport}
                href="/login"
                className="flex flex-col items-center gap-2 rounded-2xl border border-border bg-surface p-4 text-center shadow-sm transition-shadow hover:shadow-md"
              >
                <span className={`flex h-11 w-11 items-center justify-center rounded-full ${theme.light}`}>
                  <Icon size={20} strokeWidth={2.25} />
                </span>
                <span className="text-xs font-medium capitalize text-foreground">{sportLabel(sport)}</span>
              </Link>
            );
          })}
        </div>
      </section>

      {/* Search & discover */}
      <section className="py-8">
        <div className="relative overflow-hidden rounded-[2.5rem] aspect-[16/10] md:aspect-[21/9]">
          <Image
            src="/brand/hero-search.jpg"
            alt=""
            fill
            sizes="(min-width: 1280px) 1152px, 100vw"
            className="object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/25 to-transparent" />
          <div className="absolute inset-x-0 bottom-0 p-6 md:p-10">
            <h2 className="text-xl md:text-2xl font-bold text-white max-w-md text-balance">
              Find nearby courts and open games in seconds
            </h2>
            <p className="text-white/80 text-sm md:text-base mt-2 max-w-md">
              Filter by sport, city, and time — see live availability before you commit.
            </p>
            <Link href="/login">
              <Button variant="secondary" pill className="mt-4 px-6 py-2.5 text-sm">
                Explore venues
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Value props */}
      <section className="py-8">
        <div className="relative overflow-hidden rounded-[2.5rem] p-6 md:p-10">
          <Image
            src="/brand/hero-community.jpg"
            alt=""
            fill
            sizes="(min-width: 1280px) 1152px, 100vw"
            className="object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-b from-black/70 via-black/55 to-black/70" />
          <div className="relative">
            <h2 className="text-lg font-bold mb-4 text-white">Why SportsOS</h2>
            <div className="grid sm:grid-cols-3 gap-4">
              {VALUE_PROPS.map((prop) => {
                const Icon = prop.icon;
                return (
                  <Card key={prop.title} className="space-y-3 shadow-lg">
                    <span className="flex h-10 w-10 items-center justify-center rounded-full bg-indigo-50 text-indigo-600">
                      <Icon size={18} strokeWidth={2.25} />
                    </span>
                    <p className="font-semibold text-sm">{prop.title}</p>
                    <p className="text-sm text-ink-muted">{prop.description}</p>
                  </Card>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      {/* Venue owner CTA */}
      <section className="py-8 pb-16">
        <div className="rounded-3xl bg-gradient-to-r from-brand-from to-brand-to p-8 md:p-10 text-white flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <span className="hidden sm:flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-white/15">
              <Building2 size={22} strokeWidth={2.25} />
            </span>
            <div>
              <p className="text-lg font-bold">Own a sports venue?</p>
              <p className="text-white/80 text-sm mt-0.5">
                List your courts on SportsOS and start taking bookings today.
              </p>
            </div>
          </div>
          <Link href="/signup">
            <Button variant="secondary" pill className="px-6 py-3 text-sm shrink-0 flex items-center gap-1.5">
              List your venue
              <ArrowRight size={15} strokeWidth={2.5} />
            </Button>
          </Link>
        </div>
      </section>
    </div>
  );
}
