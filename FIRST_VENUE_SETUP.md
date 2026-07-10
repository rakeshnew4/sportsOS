# 🏟️ First Venue Onboarding Guide

**Status:** Ready to go live  
**Timeline:** 30 minutes setup + test bookings  
**Goals:** Validate SportsOS platform with real venue data and first transactions

---

## Phase 1: Pre-Launch (10 min)

### Step 1.1: Start the Platform

```bash
# Terminal 1
cd C:\Users\rakes\OneDrive\Desktop\sports_arena\sportsOS
python -m uvicorn app.main:app --reload

# Terminal 2
streamlit run streamlit_app.py
```

Open browser: **http://localhost:8501**

### Step 1.2: Create Venue Owner Account

In the **Sign up** tab:

```
Role:           Venue owner
UID:            venue_owner_1
Display name:   [Venue Owner Name]
Phone:          [Your phone number]
```

Click **Create account**

---

## Phase 2: Venue Setup (10 min)

### Step 2.1: Create Venue

In the **Admin** tab:

**Create a venue** form:

```
Venue name:     ABC Sports Arena
City:           Hyderabad
Latitude:       17.385
Longitude:      78.487
Sports:         badminton, cricket, tennis
```

Click **Create venue** → Note the `tenant_id`

### Step 2.2: Add Courts

Still in **Admin** tab, under your venue:

**Court 1 - Badminton**
```
Court name:     Court 1
Sport:          badminton
Hourly price:   ₹600
Open:           06:00
Close:          23:00
Dynamic pricing: OFF
```

**Court 2 - Cricket**
```
Court name:     Court 2
Sport:          cricket
Hourly price:   ₹800
Open:           06:00
Close:          23:00
Dynamic pricing: OFF
```

**Court 3 - Tennis**
```
Court name:     Court 3
Sport:          tennis
Hourly price:   ₹700
Open:           06:00
Close:          23:00
Dynamic pricing: OFF
```

---

## Phase 3: Create Test Players (10 min)

Create 3 test player accounts in **Admin** tab:

**Player 1 - Captain**
```
UID:            player_captain_1
Display name:   Arjun Sharma
Phone:          +919999999991
```

**Player 2 - Community Joiner**
```
UID:            player_2
Display name:   Priya Patel
Phone:          +919999999992
```

**Player 3 - Waitlist Tester**
```
UID:            player_3
Display name:   Rahul Singh
Phone:          +919999999993
```

---

## Phase 4: Test the First Booking Flow (20 min)

### Scenario: Book → Open to Community → Join → Promote from Waitlist

**Step 4.1: Player 1 Books Court**

Switch to `player_captain_1` in sidebar

Go to **Discover Venues** tab:
1. Find "ABC Sports Arena"
2. Select "Court 1 - Badminton"
3. Pick tomorrow 6:00 PM
4. Booking cost: ₹600
5. Status: "Confirm booking"

✅ Booking created

---

**Step 4.2: Player 1 Opens to Community**

Go to **Hybrid Booking** tab:
1. See your confirmed booking
2. Click "Open to community"
3. Set slots to open: `2`
4. Status: Now shows "🟦🟦⬜" (2 filled, 1 empty)

✅ Match is now discoverable

---

**Step 4.3: Player 2 Joins Match**

Switch to `player_2` in sidebar

Go to **Hybrid Booking** tab:
1. Find "ABC Sports Arena - Badminton - 6:00 PM"
2. Click "Join"
3. Cost: ₹600 (split 3 ways = ₹200 per player)
4. Status: "Confirmed"

✅ Second player joined

---

**Step 4.4: Player 3 Joins & Gets Waitlist**

Switch to `player_3` in sidebar

Go to **Hybrid Booking** tab:
1. Find the same match (now shows "🟦🟦🟦" — full)
2. Click "Waitlist" button
3. Position: **#1**
4. Status: "⏳ Waiting"

✅ Player 3 added to waitlist

---

**Step 4.5: Venue Staff Promotes from Waitlist**

Switch back to `venue_owner_1`

Go to **Staff Dashboard** tab:
1. Select venue: "ABC Sports Arena"
2. Go to **Waitlist** subtab
3. See: "Badminton 6:00 PM — 1 waiting — Rahul Singh (#1)"
4. Click "Promote"

What happens automatically:
- Player 3 status → "🎉 PROMOTED"
- Player 3 gets notification
- Player 3 has 30 minutes to confirm

✅ Cascade triggered

---

**Step 4.6: Promoted Player Confirms**

Switch to `player_3`

Go to **Waitlist** tab:
1. See: "🎉 PROMOTED - 30 min to confirm"
2. Click "✓ Confirm"
3. Status: "Confirmed - match slot taken"

✅ Slot confirmed, booking complete with 3 players

---

## Phase 5: Settlement Ledger (Manual for Now)

### What to track for venue owner:

Create a **settlement_abc_arena.csv** file:

```
Date,Type,Amount,Description,Balance
2026-07-09,Booking,600.00,Player 1 - Court 1 6PM,-600.00
2026-07-09,Booking,600.00,Player 2 - Court 1 6PM,-1200.00
2026-07-09,Booking,600.00,Player 3 - Court 1 6PM,-1800.00
```

At end of week (e.g., July 15):

```
Weekly Settlement - ABC Sports Arena

Period:          Jul 9–15
Total Collected: ₹1,800
Refunds:         ₹0
Platform Fee:    ₹0 (FREE during beta)
Net Payable:     ₹1,800
```

**Transfer ₹1,800 to venue owner bank account**

---

## Phase 6: What to Measure This Week

### Venue Owner Metrics

Track these in a simple spreadsheet:

| Metric | Target | How to Track |
|--------|--------|--------------|
| **Bookings/day** | 2-5 | Count confirmed bookings |
| **Revenue/day** | ₹1.2k-3k | Court price × bookings |
| **Occupancy** | >60% | Booked hours / available hours |
| **Repeat players** | >30% | See in admin user list |
| **Waitlist usage** | >1 per day | Check waitlist tab |

### Player Experience Metrics

| Metric | Target | How to Track |
|--------|--------|--------------|
| **Discovery → Booking time** | <5 min | Time from Discover to confirmed booking |
| **Join community match** | Works smoothly | Confirm hybrid booking flow works |
| **Waitlist → Promotion** | <5 sec | Test cascading promotion |
| **Confirmation rate** | >70% | 7 promoted, 5+ confirm |

---

## Phase 7: What Happens Next

### Week 1: Stability Check
- ✅ Venue owner can create courts
- ✅ Players can discover and book
- ✅ Hybrid matches work
- ✅ Waitlist promotions cascade
- ✅ Payments process cleanly
- ✅ Weekly settlement works

### Week 2: Optimization
- 🎯 Adjust court pricing based on demand
- 🎯 Add more courts if needed
- 🎯 Gather player feedback
- 🎯 Fine-tune loyalty rewards (if enabled)

### Week 3: Launch Phase 2 Venue
- Add second venue with same flow
- Test multi-venue analytics
- Validate settlement scaling

---

## Admin Commands (Troubleshooting)

### Reset demo data (if something breaks)
```
Admin tab → 🗑️ Reset demo data
```

### View all bookings
```
Admin tab → Scroll to venue
→ See "Courts" dataframe
```

### Check wallet balances
Go to **Home** tab → See "Wallet Balance" in sidebar

### View notifications sent
Go to **Notifications** tab → See all system alerts

---

## Settlement Example

### One real booking flow (numbers):

**Date:** July 9, 2026  
**Sport:** Badminton  
**Court:** Court 1  
**Time:** 6:00 PM – 7:00 PM  

```
Players: 3
Cost per player: ₹200
Total revenue: ₹600

ABC Sports Arena receives: ₹600
SportsOS platform fee: ₹0 (beta)
Net settlement: ₹600
```

**Weekly Summary (Jul 9–15):**

If you get 10 bookings × ₹600 = ₹6,000/week

At weekly settlement on **Monday, July 15:**
- Wire ₹6,000 to venue owner
- Confirm receipt
- Document in ledger

---

## Contacts & Escalations

### If a player disputes a charge:
1. Check booking details in Admin tab
2. Verify court time and price
3. If refund warranted: cancel booking (refund auto-applied)
4. Note reason in ledger

### If a venue owner wants to change pricing:
1. Go to Admin tab
2. Find venue
3. Edit court hourly_price
4. Save changes (apply to next bookings)

---

## Success Criteria

🎯 **First Week Goal:**

- [ ] Venue owner can log in and see dashboard
- [ ] At least 1 player discovers venue
- [ ] At least 1 booking confirmed
- [ ] At least 1 player joins community match
- [ ] At least 1 waitlist promotion happens
- [ ] Settlement ledger shows ≥₹1,000 collected
- [ ] No crashes or errors
- [ ] Venue owner happy with payout

---

## Next Steps After Week 1

1. **Collect Feedback**
   - Call venue owner
   - Ask: pricing, player volume, feature requests
   - Ask: what's working, what's broken

2. **Monitor KPIs**
   - Track daily bookings
   - Track repeat players
   - Track waitlist hit rate

3. **Plan Week 2**
   - Onboard 2nd venue (different sport/location)
   - Add loyalty credits if needed
   - Add referral tracking

4. **Deploy to Production**
   - After 5 venues × 2 weeks stable
   - Set up Firebase Cloud Messaging
   - Move to Streamlit Cloud or Docker

---

## File Locations

**Demo UI:** `streamlit_app.py`  
**Backend:** `app/main.py`  
**Database:** `./data/` (local JSON, then Firestore)  
**Settlement ledger:** Create in Excel/CSV in project root

---

## Questions?

- **API docs:** http://localhost:8000/docs
- **Backend logs:** Check terminal running FastAPI
- **Streamlit logs:** Check browser console (F12)

**You're ready. Go get your first venue! 🚀**
