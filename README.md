# SportsOS

API-first backend for SportsOS: FastAPI + Firestore. Current scope is the B2B demo MVP —
registration/auth, court booking, Join Match, and a player wallet. See `AGENTS.md`-equivalent
context in the repo's saved plan for the full design rationale.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env
```

By default (`DATA_BACKEND=local_json`) the app stores data in a local JSON file
(`./local_data/store.json`, gitignored) — no GCP setup needed. This is the mode to use for
dummy-data iteration and the Streamlit demo below. Switch to real Firestore only once that's
solid (see "Switching to real Firestore").

## Local dummy-data testing (Streamlit)

```bash
pip install -r requirements-dev.txt
streamlit run streamlit_app.py
```

This talks directly to `app/services/*.py` (no HTTP, no Firebase Auth — you just pick which
dummy user you're "acting as" in the sidebar) against the local JSON store. Tabs mirror the demo
flow below: register users → create a venue + courts → book a slot → open it to the community →
discover/join as another player → check wallet ledgers. A "Reset demo data" button in the sidebar
clears the local store.

You can also run the FastAPI server against the same local JSON store:

```bash
uvicorn app.main:app --reload
```

Open http://localhost:8000/docs for the interactive Swagger UI. Note: HTTP endpoints still
require a real Firebase Auth ID token regardless of `DATA_BACKEND` (see "Auth note" below) — the
Streamlit UI is the way to exercise the flow without minting real tokens.

## Switching to real Firestore

Once the demo flow is solid locally, set in `.env`:

```
DATA_BACKEND=firestore
GOOGLE_APPLICATION_CREDENTIALS=./firebase_serviceaccount.json
FIRESTORE_PROJECT_ID=<your project id>
```

`firebase_serviceaccount.json` (the GCP service account key) must then sit at the repo root —
it's gitignored. Never commit it.

For local dev against a Firestore *emulator* instead of the real project, install the Firebase
CLI (`npm install -g firebase-tools`), run `firebase emulators:start --only firestore`, and set
`FIRESTORE_EMULATOR_HOST=localhost:8080` in `.env`. Leave it blank to hit the real project.

## Auth note

FastAPI endpoints expect a Firebase Auth ID token as a Bearer token (`Authorization: Bearer
<token>`). Firebase Auth itself (sign-up/sign-in, phone OTP, etc.) happens client-side with a
Firebase client SDK — this backend only verifies the resulting ID token and layers roles/tenancy
on top. This applies regardless of `DATA_BACKEND`; the Streamlit UI bypasses it entirely by
calling the service layer directly, which is why it's the fast path for dummy-data iteration.

## Demo flow to exercise end-to-end

1. Register an owner → create a venue → add a court.
2. Register a couple of test player accounts.
3. Player A books a court slot, then opens it to the community.
4. Player B discovers it and joins.
5. Both check their wallet ledgers — the join payout (captain credited, joiner debited) should
   show up as matching transactions.

Via Streamlit, this is exactly the flow across the 5 tabs. Via HTTP, the equivalent calls are:
`POST /auth/register/owner` → `POST /venues` → `POST /venues/{tenant_id}/courts` → `POST
/auth/register/player` (x2) → `POST /venues/{tenant_id}/bookings` → `PATCH
/venues/{tenant_id}/bookings/{booking_id}/open-to-community` → `GET /matches` → `POST
/venues/{tenant_id}/bookings/{booking_id}/join` → `GET /wallet/me/transactions`.

## Notes / deferred scope

- QR check-in, dynamic pricing, membership, coaching, tournaments, and analytics are
  intentionally out of scope for this MVP (see project plan).
- Collection-group queries used for match discovery and "my bookings" need a Firestore composite
  index the first time they run against a real project (not needed in `local_json` mode, and not
  needed against the emulator) — Firestore's error message includes a direct console link to
  create it.
