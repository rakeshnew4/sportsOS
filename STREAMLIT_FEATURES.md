# 🎾 SportsOS Streamlit UI - Complete Feature List

**Status:** ✅ Production Ready  
**Date:** 2026-07-09  
**Backend:** FastAPI + Firestore  
**Frontend:** Streamlit  

---

## 🎯 Quick Start

### Windows
```bash
# Double-click this file:
run.bat
```

### macOS/Linux
```bash
chmod +x run.sh
./run.sh
```

### Manual Start
```bash
# Terminal 1 - Backend
python -m uvicorn app.main:app --reload

# Terminal 2 - Frontend
streamlit run streamlit_app.py
```

Then visit:
- **Frontend:** http://localhost:8501
- **API Docs:** http://localhost:8000/docs

---

## 📊 Dashboard Features by Role

### 👤 Player Features

#### Home Dashboard
- 💰 Wallet balance display
- 📅 Upcoming bookings (next 7 days)
- 📊 Personal KPIs:
  - Matches played this month
  - Hours played
  - Wallet spent
  - Favorite sport & venue
  - Weekly sessions
  - Repeat venue frequency
- ✨ Personalized match recommendations
- 📈 Popular sports trending at nearby venues

#### Discover Venues (Tab 2)
- 🔍 **Smart Filtering:**
  - Filter by sport (multi-select)
  - Filter by city
  - Price range slider (₹0-2000/hr)
- 🏟️ **Venue Discovery:**
  - Venue cards with name, location, sports
  - List of available courts
  - Court pricing and dynamic pricing info
- 📅 **Booking Flow:**
  - Select court
  - Choose date and time slots
  - View availability in real-time
  - Dynamic pricing explanation (if enabled)
  - Confirm booking with instant confirmation

#### My Bookings (Tab 3)
- ✅ **Active Bookings:**
  - Sport, date, time, team name (if applicable)
  - Status badge (confirmed/cancelled)
  - Open slots display (if joinable)
  - Unique booking ID
  - Cancel booking option
- ❌ **Cancelled Bookings:**
  - Historical view of past cancellations
  - Reason for cancellation

#### Hybrid Booking - Open to Community (Tab 4)
- 👥 **Open Your Booking:**
  - Select your confirmed bookings
  - Specify number of slots to open
  - Players can now discover and join
  - Real-time slot display (PUBG-style)
  - **Visual slot display:** 🟦 = filled, ⬜ = empty
- 🌐 **Discover Open Matches:**
  - Filter by sport
  - Filter by date
  - Squad composition view
  - Join button if slot available
  - View all participants
  - Can't join your own match

#### Join Match Queue - PUBG Style (Tab 5)
- 🎮 **Queue Management:**
  - Select venue and court
  - Show minimum players for sport
  - Select date and time slot
  - Queue with one click
- ⏳ **Queue Status:**
  - Real-time queue display (🟦 filled, ⬜ empty)
  - Show current count vs. minimum
  - "Match ready" indicator
  - "Need X more players" countdown
  - Auto-form when minimum reached
- 🤖 **Automatic Matching:**
  - System books court when match forms
  - Cost split equally among players
  - Instant confirmation
  - Cancel queue anytime

#### Wallet (Tab 6)
- 💳 **Wallet Overview:**
  - Current balance
  - Total credits received
  - Total debits made
  - Top-up form (demo mode)
- 📜 **Transaction Ledger:**
  - Full transaction history
  - Type (credit/debit)
  - Amount
  - Reason (booking, reward, top-up)
  - Related booking
  - Balance after transaction
  - Timestamp

#### Teams - Team Network (Tab 7) **[Phase 3]**
- ⚽ **Create Team:**
  - Team name
  - Primary sport
  - Auto-generate team ID
- 👥 **Team Management:**
  - List of your teams
  - Members per team
  - Current ELO rating (1200 baseline)
  - Win/loss record
  - Team stats card display
- 📊 **Team Details:**
  - **Members tab:**
    - Player list with join dates
    - Matches played count
  - **History tab:**
    - Recent matches (date, opponent, result, score)
    - Rating changes per match
  - **Stats tab:**
    - Total matches played
    - Win rate percentage
    - Current ELO rating
    - Rating trend (↑ last 3 matches)
- 🏆 **Team vs Team:**
  - Challenge other teams
  - Accept challenges
  - Auto-record match results
  - Update ratings automatically

#### Notifications (Tab 8) **[Phase 4]**
- 🔔 **Notification Center:**
  - Chronological list of all notifications
  - Unread badges (🔵 vs ⚪)
  - Notification types with icons:
    - 🎉 Promotion from waitlist
    - ⏳ Match needs players
    - ⚔️ Team challenges received
    - ⏰ Match reminder (30 min before)
    - ⭐ Reward earned
  - Timestamp on each notification
- ⚙️ **Preferences:**
  - 5 notification preference toggles:
    - Match Needs Players
    - Waitlist Promotion
    - Team Challenges
    - Match Reminders
    - Rewards Earned
  - One-click save preferences
- 📋 **Notification Actions:**
  - Mark as read
  - Dismiss/delete
  - Filter unread only
  - Full notification body

#### Waitlist Management (Tab 9) **[Phase 4]**
- ⏳ **Waitlist Entries:**
  - Sport, venue, date/time
  - Your position in queue
  - Queue join timestamp
  - Current status (waiting/promoted)
- 🎯 **Promoted State (30-min confirmation window):**
  - Large promotion badge (🎉 PROMOTED)
  - Time remaining to confirm
  - **Confirm slot:** Takes it immediately
  - **Decline slot:** Moves to next player, you stay in queue
- ❌ **Leave Queue:**
  - Remove yourself anytime
  - Promotes next player if you were promoted
- 🔄 **Auto-Promotion Cascade:**
  - When someone cancels → #1 promoted
  - When #1 declines → #2 auto-promoted
  - No manual intervention needed
  - Instant notifications at each step

---

### 🏢 Venue Owner/Staff Features

#### Staff Dashboard (Tab 10)
- 🏢 **Venue Selection:**
  - Dropdown of venues you own/staff
  - Only shows your managed venues
- 📊 **KPI Dashboard:**
  - Today's revenue (₹ with trend)
  - Occupancy rate (% with trend)
  - Active bookings count
  - Staff members count

#### Today's Bookings (Subtab 1)
- 📅 **Booking List:**
  - Time, sport, court, player count
  - Revenue per booking
  - Status (confirmed/waitlist)
  - Quick actions
- ➕ **Create New Booking:**
  - Manual booking form
  - Sport selection
  - Court selection
  - Date picker
  - Time range
  - Slot count
  - Price per player
  - Create button

#### Waitlist Management (Subtab 2)
- 📋 **Active Waitlists:**
  - Booking (sport, time)
  - Count of waiting players
  - Position #1 player (30-min timer)
  - Manual promote button
- 🎯 **Promote Players:**
  - Click "Promote" to move #1 to confirmed
  - Next player auto-promoted
  - Cascade continues automatically

#### Staff Members (Subtab 3)
- 👥 **Add Staff:**
  - Email input
  - Role selector (staff/owner)
  - One-click add
  - Staff appears in list immediately
- 📋 **Staff List:**
  - Name, email, role
  - Join date
  - Status (active/pending)
  - Remove option

#### Venue Analytics (Subtab 4)
- 📊 **KPI Cards:**
  - Weekly revenue (₹ with trend)
  - Average occupancy (% with trend)
  - Repeat player %
- 📈 **Revenue Chart:**
  - Line chart showing 7-day trend
  - Daily revenue breakdown
- 📋 **Court-by-Court Breakdown:**
  - Court name and sport
  - Utilization percentage
  - Bookings count
  - Individual court cards

---

### 🔐 Admin Features (Tab 11)

#### User Registration
- 🎽 **Register Player:**
  - UID (unique identifier)
  - Display name
  - Phone number
  - Auto-creates wallet
- 🏢 **Register Venue Owner:**
  - UID
  - Display name
  - Phone number
  - Owner role assigned
  - Can manage venues

#### Venue Management
- 🏗️ **Create Venue:**
  - Venue name
  - City
  - Latitude/longitude (geo-location)
  - Sports offered (comma-separated)
  - Create button
- 🛠️ **Add Courts:**
  - Court name
  - Sport
  - Hourly price (₹)
  - Open time
  - Close time
  - Dynamic pricing toggle
  - Add button

#### User Management
- 👥 **User List:**
  - Table of all registered users
  - UID, name, phone
  - Filter/sort options
  - Delete option

#### Data Management
- 🗑️ **Reset Demo Data:**
  - Clear all local JSON data
  - Reset session
  - Confirmation dialog

---

## 🔄 Complete User Flows

### Flow 1: Solo Booking → Community → Waitlist → Promotion

```
1. Player books court (My Bookings tab)
2. Player opens slots to community (Hybrid Booking tab)
3. Community player discovers match
4. Match fills some slots
5. Full match → player joins waitlist (Hybrid Booking tab)
6. Original player cancels or slot frees
7. Waitlist #1 promoted (30-min window)
8. Notifications tab shows 🎉 PROMOTED
9. Player confirms in Waitlist tab
10. Next player auto-promoted
11. Match has full squad
```

### Flow 2: Team Play → Match → History → ELO Update

```
1. Captain creates team (Teams tab)
2. Invites players to team
3. Team books court for match
4. Match is played (check-in at venue)
5. Match completion triggers:
   - Team match history recorded
   - ELO rating updated (+25 win, -20 loss)
   - Reward issued to all players
6. View team stats (Teams → Team Details → Stats)
7. See updated rating and win/loss record
8. Check match history (Teams → Team Details → History)
```

### Flow 3: Queue → Auto-Match → Cost Split

```
1. Player queues for badminton (Join Match tab)
2. Selects venue, court, date/time
3. System shows minimum (4 players for badminton)
4. Current queue: 1/4, 2/4, 3/4, 4/4
5. When 4th player queues → auto-form match
6. System instantly:
   - Books court
   - Creates booking
   - Charges each player equally
   - Sends notification to all 4
7. Players see in My Bookings
8. All see same booking ID
9. Go to venue and play!
```

### Flow 4: Venue Staff Manages Waitlist

```
1. Venue staff logs in (Staff Dashboard tab)
2. Sees "Waitlist" booking with 3 waiting
3. Position #1: Arjun (30 min timer)
4. Someone cancels → staff clicks "Promote"
5. Arjun gets notification 🎉 PROMOTED
6. Arjun has 30 min to confirm (Waitlist tab)
7. Arjun confirms → slot taken
8. Next player auto-promoted
9. Staff sees updated queue
```

### Flow 5: Personalized Recommendations

```
1. Player lands on Home tab
2. Sees "Recommended for you" section
3. Recommendations based on:
   - Favorite sport (most played)
   - Favorite venue (most visited)
   - Skill level (can match with similar)
   - Nearby venues (geo-location)
   - Popular times (when they usually play)
4. Click "Join this match" → goes to Hybrid Booking
```

---

## 🔌 API Integration Points

Each Streamlit tab makes direct calls to the FastAPI backend:

| Tab | Endpoints Called | Phase |
|-----|------------------|-------|
| Home | `/players/me`, `/bookings/me`, `/recommendations` | 1-2 |
| Discover Venues | `GET /venues`, `GET /courts`, `POST /bookings` | 1 |
| My Bookings | `GET /bookings/me`, `DELETE /bookings/{id}` | 1 |
| Hybrid Booking | `GET /matches`, `POST /matches/{id}/open`, `POST /matches/{id}/join` | 2 |
| Join Match Queue | `POST /queue/requests`, `GET /queue/requests` | 2 |
| Wallet | `GET /wallet`, `POST /wallet/topup`, `GET /wallet/transactions` | 1 |
| Teams | `POST /teams`, `GET /teams/{id}`, `GET /teams/{id}/history`, `GET /teams/{id}/stats` | 3 |
| Notifications | `GET /notifications/me`, `POST /notifications/{id}/read`, `PATCH /notifications/preferences` | 4 |
| Waitlist | `POST /bookings/{id}/waitlist`, `GET /bookings/{id}/waitlist`, `POST /waitlist/{id}/confirm` | 4 |
| Staff Dashboard | `GET /venues/{id}/bookings`, `POST /venues/{id}/staff`, `POST /bookings/{id}/waitlist/promote` | 1,4 |

---

## 🎨 UI Components

### Reusable Elements
- **Sport emoji badges** (🏸 badminton, 🏀 basketball, etc.)
- **Status badges** (✅ confirmed, ❌ cancelled, ⏳ waiting)
- **Progress bars** for occupancy, win rates
- **Metric cards** for KPI display
- **Container borders** for visual grouping
- **Forms with validation** for data entry
- **Data tables** with sorting/filtering
- **Expandable sections** for details
- **Slot display** (PUBG-style with squares)

### Color Scheme
- **Primary:** Blue (#007bff) - actions, team info
- **Success:** Green (#28a745) - confirmed, wins
- **Warning:** Orange (#ffc107) - waitlist, pending
- **Danger:** Red (#dc3545) - cancelled, losses
- **Info:** Cyan (#17a2b8) - notifications, tips

---

## 📈 Performance Metrics Tracked

### Player Metrics
- Matches played (total & monthly)
- Hours played
- Win rate (if in team)
- Favorite sport
- Favorite venue
- Weekly session frequency
- Spending (wallet debit)

### Venue Metrics
- Daily/weekly revenue
- Occupancy rate by court
- Repeat player percentage
- Booking count
- Average booking duration
- Popular sports

### Team Metrics
- Win/loss ratio
- ELO rating
- Matches played
- Member count
- Win rate percentage

### Waitlist Metrics
- Queue depth
- Promotion rate
- Confirmation rate
- Cancellation rate

---

## 🚀 Deployment Readiness

### Tested Features
✅ Local JSON backend (demo)  
✅ Firestore backend (production)  
✅ Multi-user support  
✅ Role-based access (player/owner/staff)  
✅ Real-time updates (via polling)  
✅ Responsive design  
✅ Error handling  
✅ Form validation  

### Known Limitations
- Push notifications require Firebase Cloud Messaging setup
- Real-time updates use polling (not WebSocket)
- File uploads not implemented
- SMS notifications not integrated

### Next Steps
1. ✅ Complete backend API (Phase 1-4)
2. ✅ Build Streamlit UI (this file)
3. 🔄 **Deploy to Streamlit Cloud** (optional)
4. 🔄 **Set up Firebase Cloud Messaging** (push notifications)
5. 🔄 **Create mobile app** (React Native/Flutter)
6. 🔄 **Phase 5: Community/Social features**

---

## 📞 Support

**API Documentation:** http://localhost:8000/docs (when backend running)  
**Backend Logs:** Check terminal window running FastAPI  
**Frontend Logs:** Check browser console (F12)  
**Data Files:** Check `./data/` directory for local JSON files  

**Issues?** Check `STREAMLIT_SETUP.md` troubleshooting section.

---

**🎉 You now have a complete B2B SaaS platform for sports venues!**

**Status: PRODUCTION READY**

Ship it! 🚀
