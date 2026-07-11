# UI revamp: Playo-inspired redesign

Durable tracking doc for the page-by-page visual rebuild. Reference source: `https://playo.co`
(screens fetched/downloaded 2026-07-11, content ignored — structure/tokens only). Pick this back up
here after a context reset instead of re-deriving the plan.

## Reference tokens pulled from Playo (raw HTML/CSS, saved to scratchpad)

- **Color**: primary green `#00B562` / `#00914e` (hover/dark), accent blue-violet `#3643ba`, text
  `#3B4540`, muted text `#758a80`, surfaces `#F1F3F2` / `#F2F2F4` / `#E3E8E6`, borders `#D6DCD9`. Soft
  pastel gradients for hero sections (`#c5fceb → #fff`, `#fff → #f1f3f2`), not saturated brand gradients.
- **Type**: Figtree (body/UI sans), Poiret One (decorative display serif, used sparingly), PT Sans
  (secondary serif for some headings).
- **Shape**: very generous rounding — `rounded-3xl` (1.5rem) and custom `rounded-[52px]` on hero
  imagery, **pill buttons** (`border-radius:50px`), `rounded-full` chips/avatars everywhere.
- **Patterns worth adopting**: sticky white header with centered Play/Book/Train nav; tabbed listing
  categories with live counts ("Venues 1072 · Coaching 54 · Events 4 · Memberships 48"); "Show More"
  incremental pagination instead of numbered pages; promo badges directly on cards ("FLAT 10% OFF");
  segmented onboarding (persona cards → dedicated landing pages) instead of one generic form.

## Decision: keep our brand color, adopt Playo's shapes/patterns

Our indigo→purple brand gradient (`--brand-from`/`--brand-to` in `globals.css`) is already used across
every screen in the app. Swapping to Playo's green is a global rebrand, not a "page by page" change, so
**we're keeping our existing brand palette** and importing Playo's *layout DNA* instead: pill buttons,
soft pastel gradient hero panels, tabbed-category-with-counts, promo badges, "Show More" pagination. If
this call is wrong, flag it and we'll do a palette pass separately — easy to change centrally since
everything reads from CSS variables / `sportTheme.ts`.

## Architecture change (needed before screen 1)

Our `/` today is a **gated dashboard** (`(player)/page.tsx`, `proxy.ts` redirects anyone without the
`sportsos_uid` cookie to `/login`). Playo's `/` is a **public marketing page**. To replicate it without
breaking the existing authenticated app shell:

- [x] `web/src/app/(marketing)/` — new public route group, owns `/`: header (logo + Play/Book/Train nav
      → point at `/login` for now, since venue/game browsing is still gated), hero, popular sports grid,
      city/venue teaser strip, app-download banner, footer.
- [x] Moved the existing personalized dashboard from `(player)/page.tsx` → `(player)/home/page.tsx`
      (now lives at `/home`).
- [x] `PlayerNav.tsx`: "Home" now links to `/home` (desktop sidebar + mobile bottom nav +
      `MOBILE_PRIMARY`).
- [x] `proxy.ts`: `/` is public. Logged-in users hitting `/` get redirected straight to `/home`
      (skip the marketing page once authenticated, like a normal app-shell pattern). `/login` and
      `/signup` still redirect logged-in users to `/home` (was `/`).
- [x] `(auth)/login/page.tsx` and `(auth)/signup/page.tsx`: post-auth `router.push("/")` → `router.push("/home")`.

## Page-by-page roadmap

- [x] **1. Home / landing** (`/`, public) — this session.
- [x] **2. Play / games feed** (`(player)/play/page.tsx`) — this session. `SportFilterChips` (new,
      shared component — reuse for screen 3) replaces the freeform sport text input; pill date filter;
      match cards gained a themed icon badge, price (was missing from the card entirely), team-name
      chip, and a disabled "Full" state. Queue form (Find players tab) restyled to pill inputs to match.
      Not done: no true pagination ("Show More") — `listOpenMatches` has no pagination cursor
      server-side and venue count is small enough not to fake it.
- [x] **3. Book / venues listing** (`(player)/venues/page.tsx`) — this session. Reused
      `SportFilterChips`; pill city search; live "N venues found" count; card gained a themed gradient
      banner (stand-in for Playo's venue photo — `VenueResponse` has no image field) + chevron
      affordance. Deliberately skipped: rating/reviews, distance, promo badges — `VenueResponse` has
      none of that data and it'd be fake.
- [x] **4. Venue detail** (`(player)/venues/[tenantId]/page.tsx`) — this session. Was already mostly on
      the design system (Card/EmptyState/Skeleton); swapped its bespoke sport-filter pill row for the
      shared `SportFilterChips`, now scoped via a new `sports` prop (defaults to `ALL_SPORTS`) so it only
      shows sports this venue actually offers.
- [x] **5. Booking flow** (`.../book/page.tsx`, `DateStrip`, `SlotGrid`, `BookingSummary`) — this
      session. This flow was already well-built (pill date chips, gradient slot selection, sticky
      confirm sheet) — only change was making the Clear/Confirm buttons `pill` for consistency with the
      rest of the app. Left `DateStrip`/`SlotGrid` as-is, no rework needed.
- [x] **6. Bookings list + detail** (`(player)/bookings/...`) — this session. List page was already on
      the design system, untouched. Detail page: primary action buttons (Join/Waitlist/Cancel) made
      `pill`; fixed a pre-existing unescaped-apostrophe lint error while in the file. Left the
      invite-players/rating sub-flows structurally as-is (functional, not visually stale).
- [x] **7. Wallet** (`(player)/wallet/page.tsx`) — this session. Predated the design system (raw
      `neutral-*` colors, hardcoded `bg-emerald-600` balance card, no `Card`/`EmptyState`). Rebuilt:
      balance card now uses the brand gradient (matches home/rewards), pill top-up input+button,
      transactions are `Card` rows with a credit/debit direction icon, `EmptyState` for zero transactions.
- [x] **8a. Teams** (`(player)/teams/page.tsx`, `/teams/[teamId]/page.tsx`) — prior session. These two
      predated the design system entirely (raw `neutral-*` colors, no `Card`/`Badge`/`EmptyState`/
      `Skeleton`, plain text inputs for sport). Brought in line: `SportFilterChips` reused for both the
      create-team sport picker and the browse-teams filter, `Card`-based list rows with themed icon
      badges (list page), member rows with initial-avatar circles + captain tag + invite/challenge forms
      restyled to pill inputs, and challenge status now uses the shared `Badge` component (detail page).
      Verified live: created a real team via the API and loaded both screens through the running dev
      container, no errors.
- [x] **8b. Rewards, Notifications** (`(player)/rewards`, `/notifications`) — this session. Both
      predated the design system (raw `neutral-*`, plain divs, native checkboxes). Rewards: captain
      stats moved to the brand gradient card, referral code shown in a styled chip, leaderboard tab
      switcher now matches the Play page's pill segmented control, `Card` rows throughout. Notifications:
      new shared `Switch` component (iOS-style toggle) replaces native checkboxes for preferences/invite
      settings, unread notifications get a brand-indigo left accent instead of the old emerald tint,
      invite accept/decline are now pill buttons.
- [ ] **9. Admin dashboard** (`(admin)/admin/...`) — lower priority, internal tool, less UI investment.
      Not started (venue-creation form on this page did get new fields, see below — the rest of the
      admin surface is untouched).

## Data/feature gap closure (post-Playo-audit session)

Implemented recs 1–5 from the audit report (`https://claude.ai/code/artifact/04dbfb21-3926-4af2-8333-a528989dc7e8`),
skipping #6 (distance sort) and #7 (sport metadata) as lower-value for an initial working version, and
skipping coaching/trainers, events, and gift cards entirely (no backend model, explicitly out of scope).

- [x] **Venue photos** — `tenants.cover_image_url` (URL string, no upload infra). Venue cards and the
  venue detail hero use it when set, fall back to the existing gradient banner otherwise.
- [x] **Aggregate ratings** — the backend already collected post-match ratings but never rolled them up.
  Added `GET /ratings/venues/{tenant_id}/stats` (new) and wired the already-existing
  `GET /ratings/players/{uid}/stats` + `/reviews` (previously built, never consumed) into a new player
  profile page.
- [x] **Venue description/amenities/address** — new nullable columns on `tenants`, surfaced on venue
  detail + the admin create-venue form.
- [x] **Player skill level per sport** — `users.skill_levels` JSONB, `PUT /players/me/skills`, editable
  from the new profile page. Not wired into matchmaking/filtering yet (data capture only, per scoping).
- [x] **Host name on bookings** — `bookings.created_by_name`, denormalized at booking-creation time
  (regular + matchmaking-queue auto-match paths). Shows on the Play feed card and booking detail header.
- [x] **New player profile page** (`(player)/players/[uid]/page.tsx`) — closes the gap flagged in
  `WEB_MIGRATION.md` ("no player-profile page exists"). Stats grid, rating, skill levels (editable on
  your own profile), recent reviews. Linked from booking participants, team member rows, and a new
  "My profile" nav entry.
- Migration note: no Alembic in this project (`create_all_tables()` only creates missing tables, never
  alters existing ones) — new columns were applied to the running dev Postgres with manual
  `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` statements. If you rebuild the DB from scratch, the ORM
  models already have the columns baked in, no migration needed.
- Found and fixed a real bug while wiring this up: `web/src/app/api/proxy/[...path]/route.ts` never
  exported a `PUT` handler, so every existing `PUT` call (e.g. `updateInvitePreferences` on the
  Notifications page) was silently 405ing before this session. Fixed alongside the new skills endpoint.

## Real brand assets (from `sports_assets/`)

The repo had a set of real logo/hero images sitting untracked in `sports_assets/` (AI-generated, plus
one real stock photo). Catalogued all 14, picked the ones that actually fit the product (skipped the
luxury-complex renders, the generic non-sport app-icon grid, and the sprite-sheet of sport icons — that
last one can't be sliced into individual icons without more image tooling, and our `lucide-react` icons
already cover that need better: scalable, tintable via `currentColor`). Processed with Pillow (originals
were 7–27MB each — resized/compressed before shipping):

- `web/public/brand/logo-mark.png` — square icon-only mark (background-thresholded to transparent, crops
  cleanly on both light and dark surfaces). Used in `MarketingHeader`, `MarketingFooter`, `(auth)/layout.tsx`,
  and as `web/src/app/icon.png` (the actual browser-tab favicon now, replacing the Next.js default).
- `web/public/brand/logo.png` — full icon+wordmark lockup, kept in reserve for contexts with more vertical
  room (not wired in yet).
- `web/public/brand/hero-stadium.jpg` — marketing page hero backdrop (dark scrim + our own H1/CTA on top;
  the image's own baked-in text is intentionally muted to texture, not read as content).
- `web/public/brand/hero-community.jpg` — backdrop for the "Why SportsOS" section on the marketing page.
- `web/public/brand/sport-cricket.jpg` — real photo, wired as `getSportFallbackImage()` in `sportTheme.ts`:
  when a venue has no `cover_image_url` and its primary sport is cricket, this real photo is used instead
  of the flat gradient banner (venues list card + venue detail hero). Only cricket has a real photo — every
  other sport still falls back to the gradient rather than faking a photo we don't have.
- Also gave Login/Signup (`(auth)/login`, `(auth)/signup`) the design-system pass while touching
  `AuthLayout` for the logo — this was the biggest flagged gap from the earlier page ratings (pill inputs,
  `Card`, gradient submit button, segmented role picker replacing the old bare `bg-white`/emerald styling).
- **Bug found while wiring the hero images in**: `proxy.ts`'s middleware matcher only excluded
  `_next/static`, `_next/image`, and `favicon.ico` — every other static file (including these new
  `/brand/*` images) was being routed through the auth check and redirected to `/login` for logged-out
  visitors. Exactly the pages (marketing home, login, signup) that needed them to work while logged out.
  Fixed the matcher to exclude any path ending in a file extension, verified `/brand/*` and `/icon.png`
  now serve `200` with no cookie, and that real protected routes (`/home`) still correctly redirect.

**Explicitly out of scope**: Playo's Train/coaching, gift cards, and partner-onboarding screens have no
backing feature/backend in this app (see `WEB_MIGRATION.md` — no coaching/gift-card data model exists).
Not replicating those screens until/unless the backend supports them.

## New/changed shared components introduced along the way

Track here as they're built so later screens reuse instead of re-inventing:

- `Button`: add a `pill` size/shape variant (Playo's `border-radius:50px` CTAs) alongside existing
  variants.
- Marketing-only `MarketingHeader` / `MarketingFooter` (not reused by the authenticated app shell, which
  keeps `PlayerNav`).
- `PromoBadge` — small corner/inline badge for discount-style callouts on cards (used from screen 2/3
  onward). **Still not built** — no screen has needed it yet since we don't have real promo/discount data;
  revisit only if that data shows up.
- `SportFilterChips` (`ui/SportFilterChips.tsx`) — built for screen 2, now reused on screens 3, 4, and
  8a. Takes `sports` (defaults to every sport) and `allowAll` (hide the "All" chip when a single sport is
  required, e.g. team creation) so it scopes to context instead of always showing the global sport list.
- `Switch` (`ui/Switch.tsx`) — iOS-style toggle, built for the Notifications preferences/invite-settings
  screen. Reach for this over a native checkbox anywhere else a boolean setting shows up.
