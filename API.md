# SportsOS API — KPI-First Design

## Overview

SportsOS is built KPI-first: every endpoint measures business outcomes, not just features. The API is organized by stakeholder: **players**, **venue owners**, and **platform admins**.

---

## Authentication (TODO: Firebase ID tokens)

Currently uses dummy user selection in Streamlit (local demo). Production wires Firebase Auth ID tokens via `X-Auth-Token` header.

---

## Player Endpoints

### Register & Login
- `POST /auth/register-player` — Create player account
  - **Input:** `display_name`, `phone`
  - **Output:** `uid`, `roles`, `created_at`
- `POST /auth/register-owner` — Create venue owner account
  - **Input:** `display_name`, `phone`
  - **Output:** `uid`, `roles`, `created_at`
- `GET /auth/me` — Get current user profile
  - **Output:** `uid`, `display_name`, `roles`, `wallet_balance`

### Player KPIs (North Star)
- `GET /kpis/players/{uid}/engagement?scope=month|quarter|year|all_time` — Player activity & retention
  - **Output:** `matches_played`, `courts_booked`, `hours_played`, `wallet_balance`, `favorite_sport`, `favorite_venue`, `weekly_sessions`
  - **Used by:** Player dashboard, retention analysis, personalized recommendations

### Wallet & Payments
- `GET /players/{uid}/wallet` — Current balance and transaction history
  - **Output:** `balance`, `ledger[]` with timestamps and reasons
- `POST /players/{uid}/wallet/topup` — Add funds (in-app purchase mockup)
  - **Input:** `amount`, `payment_method`
  - **Output:** `new_balance`, `transaction_id`

---

## Venue Owner Endpoints

### Venue Management
- `POST /venues` — Create venue (owner role required)
  - **Input:** `name`, `city`, `geo` (lat/lng), `sports[]`
  - **Output:** `tenant_id`, `created_at`
- `GET /venues/{tenant_id}` — Venue details
  - **Output:** `name`, `city`, `sports`, `courts[]`, `owner_uid`

### Court Management
- `POST /venues/{tenant_id}/courts` — Add court
  - **Input:** `name`, `sport`, `hourly_price`, `open_time`, `close_time`
  - **Output:** `court_id`, `created_at`
- `GET /venues/{tenant_id}/courts` — List courts
  - **Output:** `court[]` with id, name, sport, price, availability

### Bookings (Captain Role)
- `GET /venues/{tenant_id}/bookings/availability?court_id=&date=` — Check open slots
  - **Output:** `available_slots[]` with time windows
- `POST /venues/{tenant_id}/bookings` — Book a court slot
  - **Input:** `court_id`, `date`, `start_time`, `end_time`
  - **Output:** `booking_id`, `status` (confirmed), `price`, `participants[]`
- `GET /venues/{tenant_id}/bookings` — List owner's bookings
  - **Output:** `bookings[]` with status, participants, revenue
- `DELETE /venues/{tenant_id}/bookings/{booking_id}` — Cancel booking
  - **Output:** `status` (cancelled), `refund_amount`

### Hybrid Booking (Join Match variant)
- `POST /venues/{tenant_id}/bookings/{booking_id}/open-to-community` — Open slots to community
  - **Input:** `slots_open` (how many player slots to fill)
  - **Output:** `booking` with `is_joinable=true`, `slots_open`
- `GET /venues/{tenant_id}/matches?is_joinable=true` — Discover open bookings
  - **Output:** `matches[]` with slots_open, current_players, time, captain_rating

---

## Player Endpoints (Continued)

### Court Booking & Discovery
- `GET /venues/{tenant_id}/bookings/availability?court_id=&date=` — Check availability
- `POST /venues/{tenant_id}/bookings` — Book court (same as captain, but as player)
- `GET /matches?sport=&date=&location_lat=&location_lng=` — Discover open bookings
  - **Output:** `matches[]` with venue, court, sport, time, slots_open, captain_info, avg_rating

### Hybrid Booking (Join Match variant)
- `POST /venues/{tenant_id}/matches/{booking_id}/join` — Join open booking
  - **Input:** (none — deducts from wallet)
  - **Output:** `match` with your participant entry, updated wallet balance
  - **Transactional:** Wallet debit + participant addition in single transaction

### Join Match Queue (True Matchmaking)
- `POST /venues/{tenant_id}/match-requests` — Queue for a slot
  - **Input:** `court_id`, `date`, `start_time`, `end_time`
  - **Output:** `request` with `status` (waiting|matched), `current_count`, `min_players_needed`
  - **Transactional:** If `current_count >= min_players[sport]`, auto-forms booking, debits all wallets, marks all as matched
- `GET /venues/{tenant_id}/match-requests?court_id=&date=` — See queue status
  - **Output:** `requests[]` with uid, status, waiting_position
- `DELETE /venues/{tenant_id}/match-requests/{request_id}` — Cancel queue entry
  - **Output:** `status` (cancelled)

---

## Venue Owner Endpoints (Continued)

### Venue KPIs (North Star Dashboard)
- `GET /kpis/venues/{tenant_id}/overview?scope=today|week|month` — Daily business summary
  - **Output:**
    - `revenue`: `total_revenue`, `transaction_count`, `avg_transaction_value`
    - `occupancy`: `per_court[]` with utilization %, booked_hours, no_shows
    - `customers`: `active_count`, `new_count`, `repeat_percent`, `avg_lifetime_value`
    - `matchmaking`: `total_queued`, `matches_formed`, `fill_rate`, `queue_cancellations`
    - `avg_occupancy_percent`
  - **Used by:** Venue dashboard, ops reviews, dynamic pricing decisions

### Discovery & Analytics
- `GET /venues/{tenant_id}/players?sort=bookings|rating|spend` — Player roster
  - **Output:** `players[]` with total_bookings, avg_spend, repeat_rate, favorite_sport
- `GET /venues/{tenant_id}/analytics/revenue?from=2026-07-01&to=2026-07-31` — Revenue drilldown
  - **Output:** `daily[]` with revenue, bookings, avg_price, occupancy_percent

---

## Platform Admin Endpoints

### Admin KPIs (System Health)
- `GET /kpis/platform/admin` — Business health snapshot
  - **Output:**
    - `active_venues`, `total_venues`
    - `active_players`, `total_players` (DAU, MAU, WAU)
    - `bookings_today`, `bookings_this_month`
    - `matches_formed_today`, `matches_formed_this_month`
    - `gmv_today`, `gmv_this_month`, `mrr`, `arr`
    - `payment_success_rate`
    - `player_retention_7d`, `player_retention_30d`, `churn_rate`
  - **Used by:** Exec dashboard, investor updates, growth metrics

---

## Data Models

### Booking (Hybrid Booking & Queue Formation)
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
  "status": "confirmed",
  "is_joinable": false,
  "slots_total": 4,
  "slots_open": 2,
  "participants": [
    {"uid": "player_a", "joined_at": "...", "paid": true},
    {"uid": "player_b", "joined_at": "...", "paid": true}
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
    {"type": "topup", "amount": 1000, "reason": "Initial load", "at": "..."},
    {"type": "debit", "amount": 250, "reason": "Hybrid booking join", "booking_id": "...", "at": "..."},
    {"type": "credit", "amount": 100, "reason": "Referral bonus", "at": "..."}
  ]
}
```

---

## North Star Metrics (What We Measure)

### Player Level
- Matches joined this month
- Hours played
- Wallet spend
- Repeat venues
- Player rating (future)

### Venue Level
- Today's revenue
- Court occupancy %
- Active players
- Repeat customer %
- Join Match fill rate

### Platform Level
- DAU / MAU
- GMV (Gross Merchandise Value)
- MRR / ARR
- Player retention (7d, 30d)
- Churn rate

---

## Implementation Notes

- **Firestore collections:** `users`, `tenants/{id}/courts`, `tenants/{id}/bookings`, `tenants/{id}/match_requests`
- **Multi-tenancy:** Tenant-scoped queries, collection-group queries for cross-tenant discovery
- **Transactions:** Wallet debits + booking creation/participant addition are atomic (Firestore @transactional)
- **Local dev:** `DATA_BACKEND=local_json` uses fake Firestore backed by JSON file; flip to `firestore` for real GCP
- **Auth:** Currently dummy (Streamlit sidebar); production uses Firebase Auth ID tokens + role-based middleware

---

## Error Responses

All endpoints return standard HTTP status codes:
- `200 OK` — Success
- `201 Created` — Resource created
- `400 Bad Request` — Invalid input (e.g., overlapping bookings, insufficient wallet balance)
- `404 Not Found` — Resource not found
- `409 Conflict` — Business rule violation (e.g., duplicate queue entry, slot already booked)
- `500 Internal Server Error` — Server error (with detail message)

Example error response:
```json
{
  "status_code": 409,
  "detail": "Court slot already booked for this time"
}
```
