# 🚀 Launch Week Checklist

**Goal:** Take SportsOS from demo to first real venue with live bookings  
**Timeline:** 7 days  
**Outcome:** ₹5-10k in first week bookings + proven settlement flow

---

## Monday (Day 1) - Platform Prep & Pitch

### Morning
- [ ] Start backend & Streamlit locally
- [ ] Create venue owner test account
- [ ] Create 3 test player accounts
- [ ] Process 1 test booking end-to-end
- [ ] Verify settlement calculation

### Afternoon
- [ ] Identify 3 target venues (call/meet)
- [ ] Prepare pitch deck (use VENUE_OWNER_PITCH.md)
- [ ] Set up Zoom/meeting
- [ ] Print or email docs (FIRST_VENUE_SETUP.md, settlement template)

### Evening
- [ ] **Call Venue Owner #1**
  - 30 min: Pitch + demo
  - 30 min: Setup their account
  - Result: Venue live in system

**End of Day:** 1 venue owner account created, venue in system

---

## Tuesday (Day 2) - Court Setup & Go-Live

### Morning (With Venue Owner - Synchronous)
- [ ] Add their courts (2-3 courts minimum)
  - [ ] Court names
  - [ ] Sports
  - [ ] Hourly pricing
  - [ ] Hours of operation
- [ ] Show them KPI dashboard
- [ ] Answer questions
- [ ] Walk them through player flow

### Afternoon (Your Side)
- [ ] Create 5 test players with relevant location/sport preferences
- [ ] Manually add their venue to player recommendations
- [ ] Send venue owner a welcome email with:
  - [ ] Admin link
  - [ ] Settlement template
  - [ ] FAQ document

### Evening
- [ ] Monitor for early traffic
- [ ] Be on standby for questions

**End of Day:** Venue live, courts listed, ready for bookings

---

## Wednesday (Day 3) - Seeding & Validation

### Morning
- [ ] Manually create 2-3 sample bookings (using test players)
  - Sport: Whatever venue owner chose
  - Time: Popular slots (6-7 PM, weekends)
  - Price: Their pricing
  - Status: Confirmed
- [ ] Show venue owner these bookings in dashboard
- [ ] Confirm: "This is what real bookings look like"

### Afternoon
- [ ] Contact 3-5 friends/community (if allowed by venue owner)
- [ ] Say: "Try this new sports app, book [Venue Name]"
- [ ] Offer: Give them ₹100 credit for first booking
- [ ] Goal: Get 2-3 real bookings

### Evening
- [ ] Check-in with venue owner: "Any bookings yet?"
- [ ] Troubleshoot if needed
- [ ] Celebrate if bookings happened

**End of Day:** First real bookings in system (target: 2+)

---

## Thursday (Day 4) - Hybrid Matching Test

### Morning
- [ ] If bookings exist, test hybrid matching:
  - [ ] Have one player "open to community"
  - [ ] Have second player discover & join
  - [ ] Show venue owner: "Players joining players' matches"

### Afternoon
- [ ] If volume low, manually simulate:
  - [ ] Create booking #1 (player A)
  - [ ] Open to community
  - [ ] Have player B join
  - [ ] Show venue owner: ₹1,200 revenue from 1 booking

### Evening
- [ ] Email venue owner screenshots
- [ ] Highlight: "Your courts are generating revenue"
- [ ] Ask: "Can we reach out to more of your past customers?"

**End of Day:** Proved hybrid matching works, revenue flowing

---

## Friday (Day 5) - Waitlist & Promotion Test

### Morning
- [ ] If you have 2+ players in a booking, test waitlist:
  - [ ] Have third player click "Waitlist"
  - [ ] Show position #1
  - [ ] Promote from staff dashboard
  - [ ] Show 30-min confirmation window

### Afternoon
- [ ] If no waitlists naturally occurred, create one manually:
  - [ ] Booking with 2 players (2 slots full)
  - [ ] Add player #3 to waitlist
  - [ ] Promote
  - [ ] Confirm
- [ ] Send venue owner email: "Your first waitlist promotion! 🎉"

### Evening
- [ ] Daily settlement calculation
- [ ] Create first partial settlement report
- [ ] Calculate what venue owner will earn this week

**End of Day:** All major features (booking, hybrid, waitlist) validated

---

## Saturday (Day 6) - Community & Momentum

### Morning
- [ ] **With venue owner's permission**, share venue to 5-10 players via:
  - [ ] WhatsApp group
  - [ ] Instagram story
  - [ ] Direct messages
  - [ ] "Try this new sports app, free 1st booking"

### Afternoon
- [ ] Monitor bookings
- [ ] Answer player questions immediately
- [ ] Build momentum for end-of-week

### Evening
- [ ] Check total bookings for week
- [ ] Calculate revenue earned
- [ ] Prepare settlement report

**End of Day:** Week's data collection complete

---

## Sunday (Day 7) - Settlement & Review

### Morning
- [ ] Calculate final week settlement:
  - [ ] Total collections
  - [ ] Refunds (if any)
  - [ ] Platform fee (1% or free in week 1?)
  - [ ] Net payout
  - [ ] Bank details
- [ ] Prepare settlement email using SETTLEMENT_LEDGER_TEMPLATE.md

### Afternoon
- [ ] Send settlement to venue owner
- [ ] Call them: "Your first week summary"
  - [ ] Revenue earned
  - [ ] Bookings processed
  - [ ] Payout scheduled for Monday
  - [ ] Ask: Feedback? What worked? What didn't?

### Evening
- [ ] Document learnings:
  - [ ] What worked smoothly?
  - [ ] What needs fixing?
  - [ ] Player feedback?
  - [ ] Venue owner feedback?
- [ ] Plan week 2 improvements

**End of Day:** First week complete, settlement sent, feedback collected

---

## Week 1 Success Metrics

Celebrate if you hit these:

| Metric | Target | Status |
|--------|--------|--------|
| Venue owner confidence | High | ✅ |
| Bookings completed | 5+ | ✅ |
| Revenue generated | ₹3k-5k | ✅ |
| Hybrid matches | 1+ | ✅ |
| Waitlist promotions | 1+ | ✅ |
| Player reviews | Positive | ✅ |
| Settlement smooth | Yes | ✅ |

---

## Week 1 Failure Scenarios (Troubleshoot)

### "No bookings came in"

**Causes:**
- Venue not visible to players (search not working)
- Pricing too high
- Venue not promoted
- Players didn't download app

**Fix:**
- Manually add 3 bookings (your test players)
- Reduce price by 20% for first week
- Reach out to venue owner's past customers directly
- Next week: focus on player acquisition

---

### "Hybrid matching didn't happen"

**Cause:** Players don't know how to use it

**Fix:**
- Email players: "How to join matches" guide
- You manually create 1 hybrid match to demo
- Next week: improve in-app onboarding

---

### "Settlement calculation is wrong"

**Cause:** 
- Unclear pricing
- Refunds not deducted properly
- Platform fee calculation error

**Fix:**
- Double-check booking prices in admin
- Verify refund logic in code
- Send corrected settlement
- Build settlement audit trail

---

### "Venue owner unhappy"

**Cause:** Didn't meet expectations

**Fix:**
- Ask: "What would make this valuable?"
- Offer: Free platform fee next month (if needed)
- Add: Custom feature or priority support
- Plan: Onboard 2nd venue to show traction

---

## What to Document This Week

Create a **Week 1 Report** with:

```
# SportsOS First Venue - Week 1 Report

Venue: [Name]
Period: [Dates]
Owner: [Name]

## Metrics

Bookings: 5
Revenue: ₹3,400
Hybrid matches: 2
Waitlist promotions: 1
Repeat players: 2 (40%)

## What Worked

- Venue discovery was smooth
- Players liked opening to community
- Settlement was transparent
- Owner was responsive

## What Needs Fixing

- In-app onboarding for hybrid matches
- Waitlist promotion notifications (should be real-time)
- Court availability sometimes confusing

## Next Week Plans

- Add 2nd court
- Reach out to 20 past players
- Implement real-time notifications
- Onboard venue owner #2
```

---

## Prep for Week 2

By end of Sunday:

- [ ] Venue owner has ₹2-5k payout coming
- [ ] Players are happy with experience
- [ ] You know what to improve
- [ ] You're ready to onboard venue #2

---

## Key Contacts

**Venue Owner #1 Phone:** _______
**Backup contact:** _______
**Emergency contact (emergency only):** _______

---

## Daily Standup (Self Check-In)

Each day, ask yourself:

✅ Is the platform running without errors?
✅ Did venue owner respond to messages?
✅ Are bookings coming in?
✅ Are players finding the experience intuitive?
✅ Is settlement tracking working?

If all ✅: On track.
If any ❌: Fix today.

---

## Post-Launch: Week 2 Priorities

Once Week 1 is done:

1. **Venue Owner #2 onboarding** (repeat this checklist)
2. **Improve notifications** (real-time waitlist promotions)
3. **Player retention** (loyalty credits if enabled)
4. **Analytics dashboard** (show venue owner KPIs)
5. **Referral tracking** (measure word-of-mouth)

---

## You've Got This! 🏆

This is the hardest part — going from a perfect demo to messy reality with real people, real money, real expectations.

But if you hit these checkmarks, you've proven:
- Platform works for real use cases
- Players want this
- Venue owners trust you
- Settlement is transparent

That's enough to build on.

**Go live. Learn. Iterate. Scale.**

🚀
