# SportsOS API Endpoints

Complete API documentation for team management, rewards, and KPI tracking.

---

## 🎮 Teams Management (`/teams`)

### Team Discovery

**`GET /teams`** - List all active teams
```
Query params:
  - sport (optional): Filter by sport (e.g., "badminton")

Response: List[TeamResponse]
  {
    "team_id": "uuid",
    "team_name": "String",
    "sport": "badminton",
    "captain_uid": "uid",
    "captain_name": "Name",
    "status": "active|forming|completed|cancelled",
    "members": [{"uid": "uid", "display_name": "Name", "joined_at": "2026-07-09T..."}],
    "total_members": 4,
    "wins": 5,
    "losses": 2,
    "rating": 4.5,
    "created_at": "2026-07-09T...",
    "booking_id": "booking_id"
  }
```

**`GET /teams/me`** - List teams current player is in
```
Response: List[TeamResponse]
```

**`GET /teams/{team_id}`** - Get team details
```
Response: TeamResponse
```

**`POST /teams`** - Create a new team (user becomes captain)
```
Request: {
  "team_name": "Badminton Squad",
  "sport": "badminton",
  "description": "Competitive badminton team"
}

Response: TeamResponse (status = "forming")
```

### Team Members

**`GET /teams/{team_id}/members`** - List team members
```
Response: List[TeamMember]
  [{"uid": "uid", "display_name": "Name", "joined_at": "2026-07-09T..."}]
```

**`POST /teams/{team_id}/members`** - Invite player to team (captain only)
```
Request: {
  "player_uid": "player_rakesh",
  "player_name": "Rakesh Kumar"
}

Response: TeamMember
```

**`DELETE /teams/{team_id}/members/{player_uid}`** - Remove player from team
```
Response: {"success": true, "message": "Player removed"}
```

### Team-vs-Team Challenges

**`POST /teams/{team_id}/challenges`** - Create "looking for opponent" request
```
Request: {
  "sport": "cricket",
  "date": "2026-07-15",
  "time": "18:00",
  "venue_id": "venue_123",
  "skill_level": "intermediate",
  "match_format": "T20",
  "number_of_players": 11
}

Response: TeamOpponentResponse
  {
    "challenge_id": "uuid",
    "from_team_id": "team_id",
    "from_team_name": "Team Titans",
    "from_captain_uid": "captain_uid",
    "sport": "cricket",
    "date": "2026-07-15",
    "time": "18:00",
    "status": "pending",
    "created_at": "2026-07-09T..."
  }
```

**`GET /teams/{team_id}/challenges`** - List challenges from this team
```
Response: List[TeamOpponentResponse]
```

**`GET /teams/available`** - Discover available opponent challenges
```
Query params:
  - sport (optional): Filter by sport
  - date (optional): Filter by date

Response: List[TeamOpponentResponse]
```

**`POST /teams/{team_id}/challenges/{challenge_id}/accept`** - Accept an opponent challenge
```
Response: {
  "success": true,
  "message": "Challenge accepted",
  "booking_id": "booking_id",
  "match_date": "2026-07-15"
}
```

**`POST /teams/{team_id}/challenges/{challenge_id}/reject`** - Reject a challenge
```
Response: {"success": true, "message": "Challenge rejected"}
```

---

## 💰 Rewards Program (`/rewards`)

### Captain Rewards

**`GET /rewards/me/history`** - Get all rewards earned by current player
```
Response: List[RewardRecord]
  {
    "reward_id": "uuid",
    "player_uid": "uid",
    "reward_type": "match_completed|full_slots|new_player|off_peak|opponent_accepted|milestone",
    "credits_amount": 25.0,
    "reason": "Completed badminton match",
    "related_booking_id": "booking_id",
    "issued_at": "2026-07-09T...",
    "status": "issued"
  }
```

**`GET /rewards/me/captain`** - Get detailed captain statistics (current player)
```
Response: CaptainStatsResponse
  {
    "player_uid": "uid",
    "player_name": "Name",
    "matches_hosted": 12,
    "matches_completed": 11,
    "total_credits_earned": 275.0,
    "credits_this_month": 95.0,
    "new_players_invited": 5,
    "opponent_teams_invited": 3,
    "opponent_teams_accepted": 1,
    "acceptance_rate": 33.33,
    "off_peak_matches": 2,
    "recurring_matches": 1,
    "avg_credits_per_match": 22.9,
    "milestone_bonuses_earned": 1,
    "last_match_date": "2026-07-09"
  }
```

**`GET /rewards/{player_uid}/captain`** - Get captain statistics for any player (public)
```
Response: CaptainStatsResponse
```

### Leaderboards

**`GET /rewards/leaderboard/credits-monthly`** - Top captains by credits earned this month
```
Query params:
  - limit (default: 10): Number of top captains to return

Response: List[CaptainLeaderboardEntry]
  [
    {
      "rank": 1,
      "player_uid": "uid",
      "player_name": "Name",
      "credits_earned_month": 150.0,
      "matches_hosted_month": 8,
      "new_players_brought": 3,
      "acceptance_rate": 50.0
    }
  ]
```

**`GET /rewards/leaderboard/matches-hosted`** - Top captains by matches hosted this month
```
Response: List[CaptainLeaderboardEntry]
```

**`GET /rewards/leaderboard/new-players-referred`** - Top referrers (players brought to platform)
```
Response: List[CaptainLeaderboardEntry]
```

### Referral Program

**`GET /rewards/me/referrals`** - Get all players referred by current captain
```
Response: List[ReferralTracking]
  {
    "referral_id": "uuid",
    "referrer_uid": "uid",
    "referred_player_uid": "uid",
    "referred_player_name": "Name",
    "referred_at": "2026-07-01T...",
    "first_match_date": "2026-07-05T...",
    "credits_earned": 40.0,
    "referrer_ltv": 250.5
  }
```

**`GET /rewards/me/referral-earnings`** - Get referral earnings summary
```
Response: {
  "total_referrals": 5,
  "total_credits_earned": 200.0,
  "avg_ltv_per_referral": 85.5,
  "referrals_this_month": 2,
  "top_referrer_rank": 3
}
```

**`POST /rewards/me/referrals/create-code`** - Generate shareable referral code
```
Response: {
  "referral_code": "SPORTSOS_RAKES_ABC123",
  "share_link": "https://sportsos.app/join?ref=SPORTSOS_RAKES_ABC123",
  "description": "Share this code with friends. You'll earn ₹40-50 credits when they join!"
}
```

---

## ✅ Match Completion & Check-In (`/venues/{tenant_id}/bookings`)

### QR Check-In & Match Completion

**`POST /venues/{tenant_id}/bookings/{booking_id}/checkin`** - Check in a player to match
```
Request: {
  "player_uid": "player_rakesh"
}

Response: {
  "success": true,
  "message": "Player checked in",
  "booking_id": "booking_id"
}
```

**`GET /venues/{tenant_id}/bookings/{booking_id}/checkins`** - Get check-in status for match
```
Response: {
  "booking_id": "booking_id",
  "checked_in_count": 3,
  "checked_in_players": ["player_uid1", "player_uid2", "player_uid3"]
}
```

**`POST /venues/{tenant_id}/bookings/{booking_id}/complete`** - Mark match as completed (triggers rewards)
```
Request: {} (empty body)

Response: MatchCompletionResponse
  {
    "booking_id": "booking_id",
    "status": "completed",
    "completed_at": "2026-07-09T19:00:00Z",
    "players_checked_in": 4,
    "total_players": 4,
    "captain_rewards_earned": 30.0,
    "message": "Match completed! Captain earned 30 credits"
  }
```

---

## 📊 KPI Endpoints (`/kpis`)

### Platform-Wide KPIs

**`GET /kpis/platform/admin`** - System-wide health dashboard
```
Response: PlatformAdminKPI
  {
    "snapshot_date": "2026-07-09T...",
    "active_venues": 5,
    "total_venues": 8,
    "active_players": 125,
    "total_players": 250,
    "active_captains": 20,
    "daily_active_users": 45,
    "monthly_active_users": 180,
    "bookings_today": 12,
    "bookings_this_month": 350,
    "matches_formed_today": 3,
    "matches_formed_this_month": 85,
    "team_vs_team_matches_month": 8,
    "gmv_today": 7200.0,
    "gmv_this_month": 180000.0,
    "mrr": 12500.0,
    "arr": 150000.0,
    "credits_issued_this_month": 4500.0,
    "credits_redeemed_this_month": 3200.0,
    "reward_cost_percent": 2.5,
    "total_teams": 45,
    "active_teams": 32,
    "team_vs_team_acceptance_rate": 62.5,
    "new_players_this_month": 35,
    "new_players_from_referrals": 18,
    "organic_referral_rate": 51.4,
    "payment_success_rate": 99.2,
    "match_completion_rate": 87.5,
    "match_dispute_rate": 1.2,
    "player_retention_7d": 65.3,
    "player_retention_30d": 52.1,
    "churn_rate": 8.5,
    "captain_retention_30d": 78.2
  }
```

**`GET /kpis/platform/credits`** - Credits system metrics
```
Response: CreditsMetric
  {
    "period_start": "2026-07-01",
    "period_end": "2026-07-09",
    "total_credits_issued": 4500.0,
    "total_credits_redeemed": 3200.0,
    "total_credits_outstanding": 18500.0,
    "redemption_rate": 71.1,
    "avg_credits_per_captain": 225.0,
    "avg_redemption_value": 125.5,
    "cost_of_rewards": 2.5,
    "reward_roi": 40.0
  }
```

**`GET /kpis/platform/teams`** - Team network metrics
```
Response: TeamNetworkMetric
  {
    "period_start": "2026-07-01",
    "period_end": "2026-07-09",
    "teams_active": 32,
    "new_teams": 5,
    "team_vs_team_matches": 8,
    "avg_team_size": 6.5,
    "avg_team_rating": 4.2,
    "teams_with_10_plus_matches": 8,
    "friendly_challenge_count": 12,
    "challenge_acceptance_rate": 62.5,
    "repeat_matchups": 3
  }
```

**`GET /kpis/platform/referrals`** - Referral acquisition metrics
```
Response: ReferralMetric
  {
    "period_start": "2026-07-01",
    "period_end": "2026-07-09",
    "new_players_total": 35,
    "new_players_from_referrals": 18,
    "referral_rate": 51.4,
    "avg_lifetime_value_referred": 1850.5,
    "top_referrer_uid": "player_rakesh",
    "top_referrer_count": 4,
    "referral_credit_cost": 160.0
  }
```

**`GET /kpis/platform/match-completion`** - Match quality metrics
```
Response: MatchCompletionMetric
  {
    "period_start": "2026-07-01",
    "period_end": "2026-07-09",
    "matches_created": 40,
    "matches_completed": 35,
    "completion_rate": 87.5,
    "no_show_rate": 12.5,
    "avg_actual_attendance": 88.5,
    "matches_with_disputes": 2,
    "dispute_rate": 5.7,
    "reward_issued_after_completion": 35
  }
```

### Player & Venue KPIs

**`GET /kpis/venues/{tenant_id}/overview`** - Venue health dashboard
```
Query params:
  - scope (default: TODAY): today|week|month|custom

Response: VenueOverviewKPI (includes new captain rewards and match completion metrics)
```

**`GET /kpis/players/{uid}/engagement`** - Player activity statistics
```
Query params:
  - scope (default: MONTH): month|quarter|year|all_time

Response: PlayerEngagementKPI (includes credits_earned, credits_redeemed, is_captain, etc)
```

**`GET /kpis/players/{uid}/captain`** - Captain-specific reward metrics
```
Response: CaptainRewardMetric
  {
    "captain_uid": "uid",
    "captain_name": "Name",
    "period_start": "2026-07-01",
    "period_end": "2026-07-09",
    "total_credits_earned": 250.0,
    "matches_hosted": 10,
    "matches_with_full_slots": 8,
    "new_players_invited": 3,
    "opponent_teams_invited": 2,
    "opponent_teams_accepted": 1,
    "acceptance_rate": 50.0,
    "off_peak_matches": 2,
    "recurring_matches": 1,
    "milestone_bonuses_earned": 1,
    "avg_credits_per_match": 25.0
  }
```

**`GET /kpis/players/me/captain`** - Get my own captain metrics
```
Response: CaptainRewardMetric
```

---

## 📋 Reward Calculation Logic

### Reward Triggers (All issued after match completion via `/complete` endpoint)

| Action | Credits | Condition |
|--------|---------|-----------|
| Complete match | 10 | After QR check-in |
| Fill all slots | +20 | All booked slots checked in |
| New player referral | 30-50 | After first match |
| Off-peak booking | 20 | 6-10 AM or 10-11 PM |
| Opponent team accepted | 25 | After match completion |
| First new venue | 20 | After match completion |
| Recurring setup | 15 | Weekly/recurring match setup |
| Milestone: 10 matches | 100 | After 10th match |
| Milestone: 25 matches | 250 | After 25th match |
| Milestone: 50 matches | 500 | After 50th match |

### Workflow

```
1. Captain books court
   ↓
2. Captain opens to community / players join
   ↓
3. Match day: Players check in via QR
   POST /venues/{tenant_id}/bookings/{booking_id}/checkin
   ↓
4. Captain marks match complete
   POST /venues/{tenant_id}/bookings/{booking_id}/complete
   ↓
5. System calculates rewards:
   - Base match reward: ₹10
   - Full slots bonus: +₹20 (if all checked in)
   - New player referral: +₹30-50 (if any first-timers)
   - Off-peak bonus: +₹20 (if scheduled off-peak)
   - Opponent team bonus: +₹25 (if team-vs-team)
   ↓
6. Total rewards issued to wallet
   GET /wallet/me to see updated balance
```

---

## 🔗 Integration Examples

### Example 1: Match Completion Flow

```bash
# 1. Get match details
GET /venues/{tenant_id}/bookings/{booking_id}

# 2. Players check in (repeat for each player)
POST /venues/{tenant_id}/bookings/{booking_id}/checkin
  {"player_uid": "player_rakesh"}

# 3. Check final attendance
GET /venues/{tenant_id}/bookings/{booking_id}/checkins

# 4. Captain marks complete + triggers rewards
POST /venues/{tenant_id}/bookings/{booking_id}/complete

# 5. Check earned rewards
GET /rewards/me/history

# 6. Check updated wallet
GET /wallet/me
```

### Example 2: Team Challenge Flow

```bash
# 1. Captain creates opponent challenge
POST /teams/{team_id}/challenges
  {
    "sport": "cricket",
    "date": "2026-07-15",
    "time": "18:00",
    "number_of_players": 11
  }

# 2. Other captains discover challenges
GET /teams/available?sport=cricket

# 3. Opposing captain accepts
POST /teams/{accepting_team_id}/challenges/{challenge_id}/accept

# 4. Both teams play match and complete (triggers team rewards)
POST /venues/{tenant_id}/bookings/{booking_id}/complete

# 5. Both captains get opponent team bonus (+₹25 each)
```

### Example 3: Referral Tracking

```bash
# 1. Captain generates referral code
POST /rewards/me/referrals/create-code
# Returns: "SPORTSOS_RAKES_ABC123"

# 2. Friend signs up with code (handled by signup endpoint)

# 3. Friend plays first match

# 4. Check referral status
GET /rewards/me/referrals
# Shows referred friend with status and credits earned

# 5. View referral earnings
GET /rewards/me/referral-earnings
```

---

## 🎯 Health Check Endpoints

All KPI endpoints are read-only and aggregated from booking/wallet/team data.

**Key Health Indicators to Monitor:**

1. **Completion Rate** - Should be >85%
   ```
   GET /kpis/platform/match-completion
   → completion_rate > 85
   ```

2. **Reward Cost** - Should be 2-5% of GMV
   ```
   GET /kpis/platform/credits
   → cost_of_rewards between 2 and 5
   ```

3. **Referral Rate** - Should be >30% of new players
   ```
   GET /kpis/platform/referrals
   → referral_rate > 30
   ```

4. **Captain Retention** - Should be >75%
   ```
   GET /kpis/platform/admin
   → captain_retention_30d > 75
   ```

---

## 🚀 Deployment Checklist

- [ ] Update main.py with new routers (teams, rewards) ✅
- [ ] Extend team_service.py with new methods ✅
- [ ] Create rewards_service.py ✅
- [ ] Update booking_service.py with check-in/completion logic ✅
- [ ] Update kpi_service.py with new calculation functions ✅
- [ ] Update KPI models in app/models/kpi.py ✅
- [ ] Test endpoints with Streamlit UI
- [ ] Monitor reward issuance logic for edge cases
- [ ] Add logging to reward issuance for auditing

