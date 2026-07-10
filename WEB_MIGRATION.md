# SportsOS: Next.js frontend + Postgres backend migration

Context for picking this back up after a session/context reset. Streamlit (`streamlit_app.py`) is
retired — it still exists in the repo but is not being maintained and assumes the old local_json/
Firestore data model. All new frontend work happens in `web/`.

## Architecture

- **Backend**: FastAPI (`app/`) — PostgreSQL via SQLAlchemy (`app/db/orm.py`, `app/core/database.py`).
  No more Firestore/local_json — that whole abstraction (`app/core/db.py`'s old `Client`/`FieldFilter`
  shim, `app/core/fake_firestore.py`, `app/core/firebase.py`) is dead code, superseded.
- **Frontend**: Next.js 16 App Router + TypeScript + Tailwind v4 + React Query, in `web/`. Runs via
  Docker only — there is no local Node install on this machine, everything goes through
  `node:24-slim` containers.
- **Everything runs via `docker compose`** (from WSL — Docker Engine lives in the `Ubuntu-22.04` WSL
  distro, not Docker Desktop's Windows side). Windows-side `.venv`/`streamlit` processes from before
  this migration are stale, ignore them.

### Services (`docker-compose.yml`)
| Service | Port (host) | Notes |
|---|---|---|
| `postgres` | **5433** → container 5432 | Remapped from 5432 because something else on this WSL box permanently squats on host 5432 (not one of our containers — never chased down what). Backend talks to it via `postgres:5432` on the internal Docker network, so the host remap doesn't affect the app itself, only external tools (`psql`, a GUI client) connecting from Windows. |
| `backend` | 8000 | `uvicorn --reload`, bind-mounts `./app`, `DATA_BACKEND=postgresql`, `DATABASE_URL=postgresql://sportsdb:sportsdb_pass@postgres:5432/sportsdb` |
| `frontend` | 3000 | `next dev`, bind-mounts `./web`, `API_BASE_URL=http://backend:8000` (server-side only, used by Next.js route handlers) |

Tables are auto-created on backend startup (`create_all_tables()` in `app/main.py`'s lifespan) — no
migration tool, no seed data. A fresh `docker compose up` gives you empty tables; you have to
register/create venues through the API yourself (no more `local_data/store.json` seed data — that
was the old backend).

### Bring the whole stack up
```bash
# from WSL, repo root
docker compose up -d --build
docker compose logs -f backend   # or frontend
```

## Auth model (intentionally simple, matches original demo trust level)

- `POST /auth/register/player` / `/register/owner` — body is just `{display_name, phone}`, **server
  generates the uid** (no more "type your own uid"). Returns `MeResponse`.
- `POST /auth/login` — body `{phone}`, looks up the matching uid, returns `MeResponse`. No password/OTP.
- Bearer token is **always the uid itself**, unverified server-side (`app/core/security.py`). Whoever
  holds the uid acts as that user. This is a known/accepted limitation for now, not an oversight.
- Frontend hides this behind an httpOnly cookie (`sportsos_uid`) set by Next.js route handlers
  (`web/src/app/api/auth/{login,signup,logout}/route.ts`) — the browser never sees the raw uid, and all
  authenticated API calls go through `web/src/app/api/proxy/[...path]/route.ts`, which reads the cookie
  server-side and attaches `Authorization: Bearer <uid>`.
- Known limitation, not yet fixed: **one uid can't hold both player and owner roles** —
  `_create_user_doc`/`_create_user_row` in `user_service.py` 409s if the phone/uid already has a user
  row. Revisit when building the owner/admin UI (Phase 3 below).

## What's done (Phase 1 — player core flow)

Frontend (`web/src/app/(player)/`): home (quick actions + monthly stats), `/venues` discovery
(sport/city filters), venue detail + court list, full booking flow at
`/venues/[tenantId]/courts/[courtId]/book` (date strip → server-computed slot grid → +30min stepper →
confirm sheet), `/bookings` (view only, no cancel yet), `/wallet` (balance, top-up, transaction list).

Backend additions made to support this: `GET /venues` (didn't exist before — venue discovery was
impossible without it), `GET /venues/{tenant}/courts/{court}/slots` (server-computed slot grid with
availability + price, instead of making the frontend do overlap math client-side like Streamlit did),
CORS middleware.

Verified end-to-end live (both via direct `curl` and through the Next.js frontend's own auth/proxy
routes): signup → login → create venue/court (as owner) → browse → book a slot → wallet top-up → team
creation, all confirmed to actually persist across separate requests.

## Bugs found and fixed during the Postgres migration (worth knowing if you touch these files again)

Copilot's migration pattern was to paste the new SQLAlchemy version of each function *above* the old
Firestore version instead of replacing it, so most service files had duplicate function definitions —
the dead second copy still referenced deleted `Client`/`FieldFilter` types and crashed the app at
import time. Cleaned up in: `booking_service.py`, `match_service.py`, `team_service.py`,
`pricing_service.py`, `waitlist_service.py`, `notification_service.py`, `rewards_service.py`,
`matchmaking_service.py`, `kpi_service.py`.

Two systemic bugs, worth checking for if you add new mutating endpoints:
1. **`app/core/security.py` and `app/routers/kpis.py`** were calling `db = get_db()` directly instead
   of using `Depends(get_db)` — `get_db()` is a generator-based FastAPI dependency, so calling it
   directly just returns an unstarted generator, not a session. Every route needs
   `db: Session = Depends(get_db)` in its signature, never a bare call.
2. **Missing `db.commit()`** — several service functions mutate SQLAlchemy objects (or call
   `wallet_service.credit_wallet`/`debit_wallet`, which explicitly documents "caller must commit") but
   neither the service function nor the calling router ever committed, so changes silently vanished
   when the request's session closed. Fixed instances: wallet top-up
   (`app/routers/wallet.py`), match-completion rewards + team history
   (`booking_service.complete_match`), and the entire team mutation surface — create/invite/remove
   member/challenges (`app/routers/teams.py`). **If you build the owner/admin area or any other new
   mutating endpoint, double check the commit actually happens** — this codebase doesn't have a
   request-scoped auto-commit middleware, it's all manual.

## What's done (Phases 2–4 — play/lifecycle, admin, growth features)

All built frontend-only; no schema migrations. Verified end-to-end live via curl (both direct-to-backend
and through the Next proxy) and by hitting every new route through the running dev server.

- **Phase 2** (`web/src/app/(player)/play/page.tsx`, `bookings/[bookingId]/page.tsx`): unified feed with
  "Open matches" (`GET /matches` + join) and "Find players" (queue via `POST .../match-requests`).
  Booking detail page has cancel, "open to community", join, and participants list.
- **Phase 3** (`web/src/app/(admin)/admin/...`): "My venues" picker + venue creation (any logged-in
  player can create a venue — `POST /venues` already grants `owner_of` via `grant_owner_role`, so **no
  backend change was needed** for the one-uid/one-role limitation, just a reachable "create venue" UI),
  per-tenant KPI dashboard, court CRUD, staff management (add by raw uid — no name/phone search endpoint
  exists), today's bookings with check-in/complete. Gated by a `[tenantId]/layout.tsx` server component
  checking `owner_of`/`staff_of`.
- **Phase 4**: teams UI (`(player)/teams/...`), rewards/leaderboard/referrals (`(player)/rewards`),
  waitlist and post-match ratings folded into the booking detail page, notifications page + unread-count
  nav badge.
- **Backend bugs fixed along the way** (`app/services/rewards_service.py`): `list_player_rewards`,
  `get_captain_stats`, and `list_player_referrals` were building dicts that didn't match their
  Pydantic response models' required fields (`RewardRecord`, `CaptainStatsResponse`,
  `ReferralTracking`) — every rewards/captain-stats/referrals endpoint 500'd until fixed. Not related to
  the earlier Postgres migration bugs below, just discovered while wiring up the Rewards page.

## What's left

- `update_team` (`PATCH /teams/{id}`) is a real 501 stub server-side — don't build a rename-team UI
  expecting it to work until that's implemented.
- No player-profile page exists to show received ratings (`GET /ratings/players/{uid}/stats` /
  `/reviews`) — ratings can be submitted from the booking detail page but there's nowhere to view them
  yet.
- `notifications_service.py` preference updates are a stub (`PATCH /notifications/me/preferences`
  returns success but doesn't persist) — cosmetic in the UI today, worth knowing if it looks like
  toggles aren't sticking.

Full original Phase 1 plan with more detail: `C:\Users\rakes\.claude\plans\structured-forging-canyon.md`
(outside the repo, may not survive indefinitely — this file is the durable copy). Phases 2–4 plan:
`C:\Users\rakes\.claude\plans\adaptive-puzzling-gadget.md` (same caveat).

## Key file map

```
app/                          FastAPI backend
  core/database.py            SQLAlchemy engine/session factory, create_all_tables()
  core/security.py            get_current_user — bearer token IS the uid, unverified
  db/orm.py                   all 18 SQLAlchemy table models
  services/*.py                business logic — one file per domain
  routers/*.py                 thin HTTP layer, calls into services
Dockerfile.backend            backend image
web/                          Next.js frontend
  src/proxy.ts                Next 16's renamed middleware.ts — route protection
  src/app/api/auth/*           login/signup/logout route handlers (set httpOnly cookie)
  src/app/api/proxy/[...path]  same-origin catch-all → forwards to backend with Bearer token
  src/app/(auth)/              login, signup pages
  src/app/(player)/            home, venues, booking flow, bookings (+ [bookingId] detail), wallet,
                               play, teams (+ [teamId]), rewards, notifications
  src/app/(admin)/admin/       venue picker + create; [tenantId]/ layout gates on owner_of/staff_of,
                               then overview (KPIs), courts, staff, bookings (check-in/complete)
  src/components/layout/       PlayerNav.tsx, AdminNav.tsx
  src/lib/api/*.ts             typed fetch wrappers per resource
  src/lib/types.ts             hand-written TS mirrors of the Pydantic response models (snake_case)
web/Dockerfile                frontend image
docker-compose.yml            orchestrates postgres + backend + frontend
```
