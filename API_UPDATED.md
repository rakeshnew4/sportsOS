# SportsOS API — Complete Reference

## Overview

SportsOS is built **KPI-first**: every endpoint measures business outcomes. The API serves three stakeholders:
- **Players** — find matches, book courts, build reputation
- **Venue Owners** — manage facilities, analyze revenue & occupancy
- **Platform Admins** — monitor health, drive growth

---

## Authentication

Currently uses dummy user selection (local demo). Production: Firebase Auth ID tokens via `X-Auth-Token` header.

---

## Player Endpoints

### Auth
- `POST /auth/register-player` — Create player account (status 201)
  - Input: `display_name`, `phone`
  - Output: `uid`, `roles`, `created_at`
- `POST /auth/register-owner` — Create venue owner account (status 201)
  - Input: `display_name`, `phone`
  - Output: `uid`, `roles`, `created_at`
- `GET /auth/me` — Get current user profile
  - Output: `uid`, `display_name`, `roles`, `wallet_balance`

### Profile & Discovery
- `GET /players/me/profile` — Current player's detailed profile
  - Output: `uid`, `display_name`, `total_bookings`, `total_matches_played`, `total_hours_played`, `favorite_sport`, `repeat_venues_count`, `avg_rating`
- `GET /players/{uid}/profile` — Get any player's public profile
  - Output: (same as above, except phone hidden)
- `GET /players/search?sport=badminton&min_hours_played=10` — Find players by skill/sport
  - Query: `sport` (optional), `min_hours_played` (optional)
  - Output: `{ players: [...], total: N }`

### Wallet & Payments
- `GET /wallet/me` — Get wallet balance
  - Output: `balance`, `ledger[]`
- `GET /wallet/me/transactions` — List all transactions
  - Output: `list[WalletTransaction]` with type, amount, reason, timestamp
- `POST /wallet/me/topup` (status 201) — Add funds
  - Input: `amount`, `reason` (optional)
  - Output: `balance`, `transaction_id`

### Court Booking & Discovery
- `GET /venues/{tenant_id}/bookings/availability?court_id=&date=YYYY-MM-DD` — Check open slots
  - Output: `{ open_slots: [...], booked_slots: [...] }`
- `POST /venues/{tenant_id}/bookings` (status 201) — Book a court slot
  - Input: `court_id`, `date`, `start_time`, `end_time`
  - Output: `BookingResponse` with `booking_id`, `price`, `status`
- `GET /players/me/match-history?limit=20` — All past bookings/matches
  - Output: `[{ booking_id, date, sport, venue_name, participants_count, price_paid, status }]`

### Hybrid Booking (Captain + Joiners)
- `PATCH /venues/{tenant_id}/bookings/{booking_id}/open-to-community` — Open slots to players
  - Input: `slots_open` (how many to fill)
  - Output: `BookingResponse` with `is_joinable=true`
- `GET /matches?sport=badminton&date=2026-08-01` — Discover open matches
  - Output: `list[MatchResponse]` with venue, court, slots_open, participants, captain_rating
- `POST /venues/{tenant_id}/bookings/{booking_id}/join` (status 201) — Join an open match
  - Input: (none; auto-debits wallet)
  - Output: `BookingResponse` with updated wallet
  - **Transactional:** wallet debit + participant addition atomic

### Join Match Queue (True Matchmaking)
- `POST /venues/{tenant_id}/match-requests` (status 201) — Queue for a slot (no booking yet)
  - Input: `court_id`, `date`, `start_time`, `end_time`
  - Output: `{ request_id, status: waiting|matched, current_count, min_players, matched_booking_id? }`
  - **Auto-formation:** once `current_count >= MIN_PLAYERS[sport]`, system forms booking & charges all
- `GET /venues/{tenant_id}/match-requests?court_id=&date=` — See queue progress
  - Output: `[{ request_id, uid, status, waiting_position, current_count, min_players }]`
- `DELETE /venues/{tenant_id}/match-requests/{request_id}` — Leave queue
  - Output: `{ status: cancelled }`

### Ratings & Social
- `POST /ratings/` (status 201) — Rate a player after a match
  - Input: `rated_uid`, `booking_id`, `rating` (1-5), `comment` (optional)
  - Output: `RatingResponse` with `rating_id`, `created_at`
  - **Constraint:** Only match participants can rate each other; one rating per player per booking
- `GET /ratings/players/{uid}/stats` — Get player's rating summary
  - Output: `{ avg_rating, total_ratings, rating_distribution: { 1: count, 2: count, ... } }`
- `GET /ratings/players/{uid}/reviews?limit=10` — Recent reviews for a player
  - Output: `[{ from_uid, rating, comment, created_at }]`

### Analytics & Performance
- `GET /analytics/players/me/stats` — Player's match statistics
  - Output: `{ total_matches, matches_this_month, matches_this_week, favorite_sport, favorite_day_of_week, avg_participants }`
- `GET /kpis/players/{uid}/engagement?scope=month|quarter|year|all_time` — Player KPI (north star)
  - Output: `{ matches_played, courts_booked, hours_played, wallet_spend, favorite_sport, repeat_venues, avg_rating }`

---

## Venue Owner Endpoints

### Venue Management
- `POST /venues` (status 201) — Create venue
  - Input: `name`, `city`, `geo: { lat, lng }`, `sports[]`
  - Output: `VenueResponse` with `tenant_id`, `created_at`
- `GET /venues/{tenant_id}` — Get venue details
  - Output: `name`, `city`, `sports[]`, `courts[]`, `owner_uid`

### Court Management
- `POST /venues/{tenant_id}/courts` (status 201) — Add court to venue
  - Input: `name`, `sport`, `hourly_price`, `open_time`, `close_time`
  - Output: `CourtResponse` with `court_id`
- `GET /venues/{tenant_id}/courts` — List venue's courts
  - Output: `[{ court_id, name, sport, hourly_price, availability }]`

### Bookings
- `GET /venues/{tenant_id}/bookings` — List all bookings (as owner)
  - Output: `[BookingResponse]` with participants, revenue
- `GET /venues/{tenant_id}/bookings/availability?court_id=&date=` — Check open slots
  - Output: `AvailabilityResponse`

### Hybrid Booking (Owner as Captain)
- `PATCH /venues/{tenant_id}/bookings/{booking_id}/open-to-community` — Open slots
  - Input: `slots_open`
  - Output: `BookingResponse`
- `GET /venues/{tenant_id}/matches?is_joinable=true` — Discover open matches at venue
  - Output: `[MatchResponse]` with slots_open, fill_rate

### Revenue & Analytics
- `GET /venues/{tenant_id}/players?sort=bookings|spend|recent` — Roster of regular players
  - Output: `[{ uid, display_name, total_bookings, total_spend, favorite_sport, last_booking }]`
- `GET /venues/{tenant_id}/analytics/revenue?from_date=2026-07-01&to_date=2026-07-31` — Revenue drilldown
  - Output: `{ daily_data: [{ date, revenue, bookings_count, avg_price, occupancy_percent }], total_revenue, date_range }`
- `GET /analytics/venues/{tenant_id}/sport-trends?weeks=4` — Sport-wise activity trends
  - Output: `[{ sport, week_starting, matches_count, hours_played, total_revenue }]`
- `GET /analytics/venues/{tenant_id}/peak-hours` — Booking heatmap (by hour)
  - Output: `{ "18:00": 5, "19:00": 8, ... }`

### Venue KPI (North Star Dashboard)
- `GET /kpis/venues/{tenant_id}/overview?scope=today|week|month` — Daily business summary
  - Output: `{
      revenue: { total_revenue, transaction_count, avg_transaction_value },
      occupancy: [{ court_id, utilization_percent, booked_hours, no_shows }],
      customers: { active_count, new_count, repeat_percent, avg_lifetime_value },
      matchmaking: { total_queued, matches_formed, fill_rate, cancellations },
      avg_occupancy_percent
    }`

---

## Platform Admin Endpoints

### System Health
- `GET /kpis/platform/admin` — Business health snapshot (north star)
  - Output: `{
      active_venues, total_venues,
      active_players, total_players, daily_active_users,
      bookings_today, bookings_this_month,
      matches_formed_today, matches_formed_this_month,
      gmv_today, gmv_this_month, mrr, arr,
      payment_success_rate,
      player_retention_7d, player_retention_30d, churn_rate
    }`

---

## Data Models

### Booking (Hybrid & Queue-Formed)
```json
{
  "booking_id": "abc123",
  "tenant_id": "venue_1",
  "court_id": "court_1",
  "created_by": "player_a",
  "date": "2026-08-01",
  "start_time": "18:00",
  "end_time": "19:00",
  "sport": "badminton",
  "price": 500,
  "status": "confirmed|cancelled",
  "is_joinable": false,
  "slots_total": 4,
  "slots_open": 2,
  "participants": [
    { "uid": "player_a", "joined_at": "...", "paid": true },
    { "uid": "player_b", "joined_at": "...", "paid": true }
  ],
  "created_at": "2026-07-09T18:00:00Z"
}
```

### MatchRequest (Join Match Queue)
```json
{
  "request_id": "req_xyz",
  "tenant_id": "venue_1",
  "court_id": "court_1",
  "uid": "player_c",
  "sport": "badminton",
  "date": "2026-08-01",
  "start_time": "18:00",
  "end_time": "19:00",
  "status": "waiting|matched|cancelled",
  "current_count": 2,
  "min_players": 4,
  "matched_booking_id": null,
  "created_at": "2026-07-09T17:55:00Z"
}
```

### Player Wallet
```json
{
  "balance": 750.0,
  "ledger": [
    { "type": "topup", "amount": 1000, "reason": "Initial load", "at": "..." },
    { "type": "debit", "amount": 250, "reason": "Hybrid booking join", "booking_id": "...", "at": "..." },
    { "type": "credit", "amount": 100, "reason": "Referral bonus", "at": "..." }
  ]
}
```

### Rating
```json
{
  "rating_id": "r_123",
  "from_uid": "player_a",
  "to_uid": "player_b",
  "booking_id": "booking_xyz",
  "rating": 5,
  "comment": "Great player!",
  "created_at": "2026-07-09T20:30:00Z"
}
```

---

## North Star Metrics (What We Measure)

### Player Level
- Matches joined this month
- Hours played
- Wallet spend & balance
- Repeat venues
- Player rating (1-5 avg)

### Venue Level
- Today's revenue
- Court occupancy %
- Active players (30d)
- Repeat customer %
- Join Match fill rate

### Platform Level
- DAU / MAU / WAU
- GMV (Gross Merchandise Value)
- MRR / ARR
- Player retention (7d, 30d)
- Churn rate
- Payment success rate

---

## Status Codes

- `200 OK` — Success
- `201 Created` — Resource created
- `400 Bad Request` — Invalid input or business rule violation
- `403 Forbidden` — Access denied (not your booking, etc.)
- `404 Not Found` — Resource missing
- `409 Conflict` — Duplicate entry or state violation (e.g., already rated)
- `500 Internal Error` — Server error

Error response:
```json
{
  "status_code": 400,
  "detail": "Court slot already booked for this time"
}
```

---

## Implementation Notes

- **Collections:** `users`, `tenants/{id}/courts`, `tenants/{id}/bookings`, `tenants/{id}/match_requests`, `ratings`
- **Multi-tenancy:** Scoped queries + collection-group queries for cross-tenant discovery
- **Transactions:** Wallet debits + booking creation/participant addition are atomic (Firestore @transactional)
- **Local dev:** `DATA_BACKEND=local_json` uses JSON file; flip to `firestore` for GCP
- **Auth:** Currently dummy (demo); production: Firebase ID tokens + role-based middleware
- **Matching:** Same sport + date + exact time slot match on MVP; AI-tier matching (skill, geo) later
