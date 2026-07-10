# SportsOS Scripts

Utility scripts for managing SportsOS.

## Available Scripts

### 1. Generate Test Data
**File:** `generate_test_data.py`

Populate the database with dummy users, venues, courts, and bookings for testing.

**Usage:**
```bash
python scripts/generate_test_data.py
```

**What it creates:**
- 8 dummy players with ₹5000 wallet each
- 2 dummy venue owners
- 3 dummy venues with multiple courts
- Badminton, Tennis, Table Tennis, Cricket, Volleyball courts
- Sample bookings for today
- Some open matches ready to join

**Test Login IDs:**
- `player_rakesh` — Rakesh Kumar
- `player_priya` — Priya Singh
- `player_amit` — Amit Patel
- `player_neha` — Neha Sharma
- `player_vikram` — Vikram Reddy
- `player_isha` — Isha Gupta
- `player_arun` — Arun Kumar
- `player_deepak` — Deepak Verma

All players start with ₹5000 in their wallet.

**What happens when you run it:**
```
🎮 SportsOS Test Data Generator
============================================================
📝 Creating dummy players...
  ✅ Rakesh Kumar (wallet: ₹5000)
  ✅ Priya Singh (wallet: ₹5000)
  ...

🏢 Creating dummy venue owners...
  ✅ Raj Menon
  ✅ Preet Kaur

🏟️  Creating dummy venues and courts...
  ✅ Champions Sports Arena (ID: venue_123)
     • Court A (badminton) — ₹600/hr
     • Court B (badminton) — ₹600/hr
  ...

📅 Creating dummy bookings...
  ✅ player_rakesh booked 06:00-07:00 — Team: Badminton Team

🎯 Opening matches for community...
  ✅ Opened badminton match — 2026-07-09 06:00-07:00

📊 TEST DATA SUMMARY
✅ Test data generation complete!
```

## How to Use

### Step 1: Generate Test Data
```bash
cd sportsOS
python scripts/generate_test_data.py
```

### Step 2: Start Streamlit App
```bash
streamlit run streamlit_app.py
```

### Step 3: Log In
- **Phone number:** Leave blank (or use any value)
- **Tab:** Sign up
- **Role:** Player
- **UID:** `player_rakesh` (or any other test player)
- **Name:** Rakesh Kumar
- **Phone:** Any value (not used in test mode)

### Step 4: Explore Features
- View available matches in "🔍 Discover Venues"
- Queue for matches in "🎮 Join Match (queue)"
- Create bookings as a captain
- Join open matches as a community member
- Check your wallet balance and transactions

## Resetting Test Data

To clear all test data and start fresh:

### Option 1: Using Streamlit UI
1. Go to "⚙️ Admin" tab
2. Click "🗑️ Reset demo data" button
3. Confirm the reset

### Option 2: Using Python
```bash
python scripts/reset_data.py
```

### Option 3: Manual
Delete the local data file:
```bash
rm sportsOS/local_data.json
```

Then run `generate_test_data.py` again.

## Tips for Testing

### Test Different Scenarios

**Scenario 1: Hybrid Booking**
1. Log in as `player_rakesh`
2. Go to "📅 My Bookings"
3. Create a venue (if needed)
4. Create a court
5. Book a court
6. Open slots to community
7. Switch user to `player_priya`
8. Join the match from "🤝 Hybrid Booking" tab

**Scenario 2: Queue Matching**
1. Log in as `player_amit`
2. Go to "🎮 Join Match (queue)"
3. Queue for a badminton slot
4. Switch to `player_neha`, `player_isha`, `player_arun`
5. Have them queue for the same slot
6. When 4 players queue, match auto-forms
7. Check notifications

**Scenario 3: Multiple Teams**
1. Create different bookings with different team names
2. Have different players join different teams
3. View team rosters in the app

### Testing Wallets
- All players start with ₹5000
- Joining a match costs their share
- Create a booking (₹500-900), then have 2 others join
- Each person pays ~₹250-300 for their share

### Checking Teams
1. Open a match you created
2. Expand "👥 Players" to see team members
3. Try joining from another account
4. Refresh to see updated team roster

## Troubleshooting

**"Script not found"**
- Make sure you're running from the `sportsOS` directory
- Use: `python scripts/generate_test_data.py` (not just `generate_test_data.py`)

**"ImportError: No module named 'app'"**
- Make sure you're in the `sportsOS` directory
- The script adds parent directory to Python path automatically

**"Database error"**
- Check that `DATA_BACKEND=local_json` in your `.env` file
- Make sure the local data file exists: `local_data.json`

**Test data not appearing**
- Restart the Streamlit app after running the script
- Check the console output for errors
- Try resetting data and running again

## Advanced: Customizing Test Data

Edit `generate_test_data.py` to:
- Add more players
- Create different venues/cities
- Change court prices
- Adjust booking times
- Add different sports

Then run again to generate new data.

---

**Happy Testing! 🎾**
