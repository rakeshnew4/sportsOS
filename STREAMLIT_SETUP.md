# SportsOS Streamlit UI Setup

## Overview

The Streamlit UI provides a complete demo interface for all Phase 1-4 features:
- **Phase 1:** Venue OS (court management, bookings, staff access)
- **Phase 2:** Community Booking (hybrid matches, player discovery)
- **Phase 3:** Team Network (team creation, stats, history)
- **Phase 4:** Growth Engine (notifications, waitlists, auto-promotion)

## Prerequisites

1. **Python 3.10+** installed
2. **FastAPI backend running** (see instructions below)
3. **Streamlit installed** (pip install streamlit)

## Installation

### 1. Install Dependencies

```bash
pip install streamlit requests pandas
```

### 2. Set Up Environment

Create a `.streamlit/secrets.toml` file in the project root:

```toml
# .streamlit/secrets.toml
API_BASE_URL = "http://localhost:8000"
DATA_BACKEND = "local_json"  # Change to "firestore" for production
```

### 3. Start the FastAPI Backend

In one terminal window:

```bash
# From project root
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at `http://localhost:8000`

### 4. Run Streamlit UI

In another terminal window:

```bash
# From project root
streamlit run streamlit_app.py
```

The UI will open at `http://localhost:8501`

## Tabs & Features

### 🏠 Home
- Quick overview of wallet balance, bookings, and stats
- Player KPIs for current month
- Upcoming bookings
- Personalized recommendations

### 🔍 Discover Venues
- Filter venues by sport, city, price range
- Browse available courts
- Create bookings with dynamic pricing

### 📅 My Bookings
- View confirmed and cancelled bookings
- Manage courts (if venue owner)
- Create new venues
- Add courts with dynamic pricing options

### 🤝 Hybrid Booking
- Open team bookings to community players
- Discover open matches
- Join teams in progress
- Visual PUBG-style slot display

### 🎮 Join Match (Queue)
- Queue for PUBG-style matchmaking
- Auto-form matches when minimum players queue
- View queue status and requirements
- Automatic cost splitting

### 💰 Wallet
- View balance and transaction history
- Top up wallet (demo mode)
- Track spending by booking

### 👥 Teams (Phase 3)
- Create and manage teams
- View team statistics (rating, wins/losses)
- See team match history
- Manage team members
- Track ELO rating progression

### 📢 Notifications (Phase 4)
- View all notifications (match alerts, promotions, rewards)
- Configure notification preferences
- Mark as read / dismiss
- Real-time notification types:
  - 🎉 Waitlist promotions
  - ⏳ Match needs players
  - ⚔️ Team challenges
  - ⏰ Match reminders
  - ⭐ Rewards earned

### ⏳ Waitlist (Phase 4)
- View your position in queues
- Receive 30-minute confirmation window when promoted
- Confirm or decline promotion
- Auto-promotes next player if you decline
- Leave queue option

### 🏢 Staff Dashboard (Phase 1)
- **Venue owners/staff only**
- View today's bookings
- Manage active waitlists and manually promote
- Add/remove staff members
- View venue analytics:
  - Revenue tracking
  - Occupancy rates
  - Court utilization
  - Player retention metrics

### ⚙️ Admin
- Register test accounts (player or venue owner)
- View all registered users
- Manage venues and courts
- Reset demo data

## Demo Users

### Quick Start Users

Pre-create test accounts using the Admin tab or by modifying the signup flow:

**Player:**
- UID: `demo_player_1`
- Name: Demo Player
- Phone: +919999999999

**Venue Owner:**
- UID: `demo_owner_1`
- Name: Demo Owner
- Phone: +918888888888

## Data Persistence

The Streamlit app supports two backends:

### Local JSON (Default - Demo)
- Data stored in local JSON files
- No external dependencies
- Perfect for testing
- Data stored in configured data path

### Firestore (Production)
- Cloud-hosted Firebase Firestore
- Requires Firebase credentials
- Set `DATA_BACKEND=firestore` in `.env`
- Configure Firebase in `app/core/config.py`

## Key Features Walkthrough

### Creating a Booking (Team → Community)

1. **Login** as a player or venue owner
2. Go to **My Bookings** tab
3. **Discover Venues** → select a court → book a time slot
4. Go to **Hybrid Booking** tab
5. Click **"Open to community"** on your confirmed booking
6. Set number of slots to open
7. Players can now **"Join"** your match

### Waitlist Flow

1. Navigate to **Hybrid Booking** → discover an **open match**
2. If **all slots full**, click **"Waitlist"** instead of "Join"
3. You'll get added to queue with position number
4. When someone cancels → automatic promotion
5. You receive **notification** (if notifications enabled)
6. Go to **Waitlist** tab → see promotion with 30-min timer
7. Click **"✓ Confirm"** to take the slot
8. Next person auto-promoted instantly

### Team Management

1. Go to **Teams** tab
2. Click **"➕ Create Team"**
3. Enter team name, select sport
4. View team stats (rating, wins/losses)
5. See match history and member list
6. ELO rating updates after each match

### Notifications & Preferences

1. Go to **Notifications** tab
2. View all system notifications
3. Click **"⚙️ Preferences"** to configure:
   - Match needs players
   - Waitlist promotions
   - Team challenges
   - Match reminders
   - Reward notifications
4. Save preferences → system filters notifications automatically

### Staff Management

1. **Login as venue owner**
2. Go to **Staff Dashboard** tab
3. Select your venue
4. In **Staff** subtab, click **"➕ Add Staff"**
5. Enter email and select role (staff or owner)
6. Staff member appears in list with status
7. Staff can manage:
   - Today's bookings
   - Waitlist promotions
   - Venue analytics

## Architecture

```
┌─────────────────────────────────────────┐
│        Streamlit UI (Port 8501)         │
│  (streamlit_app.py)                     │
└──────────────────┬──────────────────────┘
                   │
        (HTTP Requests via requests lib)
                   │
                   ▼
┌─────────────────────────────────────────┐
│    FastAPI Backend (Port 8000)          │
│  (app/main.py)                          │
│  ├─ Auth endpoints                      │
│  ├─ Booking service                     │
│  ├─ Team service (Phase 3)              │
│  ├─ Notification service (Phase 4)      │
│  ├─ Waitlist service (Phase 4)          │
│  └─ Staff management (Phase 1)          │
└──────────────────┬──────────────────────┘
                   │
        (Firestore API calls)
                   │
                   ▼
┌─────────────────────────────────────────┐
│         Firestore Database              │
│  ├─ users/                              │
│  ├─ tenants/                            │
│  ├─ teams/                              │
│  └─ notifications/                      │
└─────────────────────────────────────────┘
```

## Troubleshooting

### "Connection refused" on startup
- **Check:** Is the FastAPI backend running on port 8000?
- **Fix:** Run `python -m uvicorn app.main:app --reload` in terminal

### "ModuleNotFoundError" for firebase_admin
- **Check:** Is DATA_BACKEND set to "firestore"?
- **Fix:** Use `DATA_BACKEND=local_json` for demo, or install `pip install firebase-admin`

### "No notifications available"
- **Check:** Is `notifications_service` module imported?
- **Fix:** Ensure all Phase 4 files are in place (see PHASE_1_TO_4_COMPLETE.md)

### Data not persisting
- **Check:** Is local data path configured correctly?
- **Fix:** Ensure `.env` has valid `LOCAL_DATA_PATH` (usually `./data/`)

### Waitlist promotion not triggering
- **Check:** Is `booking_service.cancel_booking()` wired to `waitlist_service.promote_from_waitlist()`?
- **Fix:** Verify integration in `app/services/booking_service.py` line ~250

## Running Full End-to-End Demo

```bash
# Terminal 1: Start backend
cd sports_arena/sportsOS
python -m uvicorn app.main:app --reload

# Terminal 2: Start Streamlit UI
streamlit run streamlit_app.py

# Terminal 3 (optional): Monitor logs
tail -f app.log
```

Then:
1. **Open** `http://localhost:8501`
2. **Sign up** as a player
3. **Discover a venue** and book a court
4. **Open to community** (hybrid booking)
5. **Switch user** in sidebar to another player
6. **Join** the match or waitlist
7. **Promote from waitlist** in venue staff dashboard
8. **Confirm promotion** in waitlist tab
9. **View team stats** in teams tab
10. **Check notifications** in notifications tab

## Performance Notes

- Local JSON backend: ~5-50ms response times
- Firestore backend: ~100-300ms response times
- Streamlit reruns on every interaction (optimized with caching where possible)
- For production, consider:
  - Streamlit Cloud or Docker deployment
  - FastAPI + Gunicorn with multiple workers
  - Firebase Realtime Database for live updates

## Security (Production)

For production deployment:
1. **Enable authentication** (Firebase Auth or OAuth2)
2. **Use HTTPS** (SSL certificates)
3. **API key rotation** (monthly)
4. **Rate limiting** (100 req/min per IP)
5. **Input validation** (pydantic models)
6. **CORS configuration** (restrict origins)

See `app/core/security.py` for auth details.

## Next Steps

1. ✅ **Complete:** Phase 1-4 backend API
2. ✅ **Complete:** Streamlit UI with all features
3. **Next:** Deploy to staging environment
4. **Next:** Integrate Firebase Cloud Messaging for push notifications
5. **Next:** Mobile app (React Native or Flutter)
6. **Next:** Phase 5 (Community/Social features)

---

**Need help?** Check `app/main.py` for API endpoint documentation or run `uvicorn app.main:app --help` for server options.
