# SportsOS KPI Framework

Strategic metrics for measuring platform health, growth, and the effectiveness of the rewards ecosystem.

---

## 🎯 North Star Metric

**Monthly Active Captains × Avg Match Completion Rate × Avg Team Size**

This represents the platform's core value creation: **active organizers creating matches with engaged teams.**

---

## 📊 Platform-Level KPIs (`PlatformAdminKPI`)

### Growth Metrics

| KPI | Healthy Range | Why It Matters |
| --- | --- | --- |
| **Monthly Active Users** | Week-over-week growth ≥5% | Measures platform adoption |
| **New Players This Month** | 10-15% of active user base | Growth signal; sanity check |
| **New Players From Referrals** | >30% of new players | Organic viral loop activation |
| **Active Captains** | 15-25% of active players | Network effect: more hosts → more games |
| **Total Teams** | Growing 5-10% monthly | Community formation indicator |
| **Team-vs-Team Matches** | Growing faster than individual bookings | Maturity signal: network effects working |

### Revenue & Economics

| KPI | Healthy Range | Why It Matters |
| --- | --- | --- |
| **GMV This Month** | Growing month-over-month | Platform scaling; monetization health |
| **Credits Issued** | 2-5% of GMV | Sustainable reward cost; not bleeding value |
| **Credits Redeemed** | >70% of issued | Players trust credits; not hoarding |
| **Reward Cost %** | 2-5% | ROI on rewards is 20-50x (sustainable) |
| **Organic Referral Rate** | >30% | Rewards are working; captains actively recruiting |

### Quality & Retention

| KPI | Healthy Range | Why It Matters |
| --- | --- | --- |
| **Match Completion Rate** | >85% | Matches actually happen; QR check-in working |
| **Match Dispute Rate** | <2% | Payment/logistics issues minimal |
| **Player Retention (30d)** | >60% | Sticky engagement; repeated use |
| **Captain Retention (30d)** | >75% | Captains are more loyal than casual players |
| **Churn Rate** | <15% | If too high, check: rewards not valuable? Bad experiences? |

---

## 🏆 Captain Rewards Program (`CaptainRewardMetric`)

### Program Effectiveness

| KPI | Healthy Range | Why It Matters |
| --- | --- | --- |
| **Avg Credits per Match** | ₹15-₹30 | Meaningful but modest reward |
| **Matches Hosted (per captain)** | 4+ in 30d = healthy captain | Recurring activity > one-time boosters |
| **Matches with Full Slots** | >70% | Rewards are working: captains filling teams |
| **New Players Invited** | 1-2 per captain annually | Acquisition channel is active |
| **Acceptance Rate (Opponents)** | >40% | Team challenges are engaging; not being ignored |

### Reward Tiers

**Tier 1: Match Completion (Issued immediately after QR check-in)**
- Complete a hosted match: **₹10**
- Fill all player slots: **+₹20** (bonus)

**Tier 2: Growth (Issued after match completes)**
- Bring a new player: **₹30-50** (one-time per referral)
- Off-peak booking bonus: **₹20** (6 AM, 10 PM, weekdays)
- Recurring weekly match: **₹15** (setup bonus)

**Tier 3: Team Engagement (Issued after match completes)**
- Opponent team accepted challenge: **₹25**
- First booking at new venue: **₹20**

**Tier 4: Milestones (Issued after nth match completes)**
- 10 successful hosted matches: **₹100**
- 25 matches: **₹250**
- 50 matches: **₹500**

**Key rule:** Rewards only issued **after QR check-in confirms match completion.**

---

## 💳 SportsOS Credits System (`CreditsMetric`)

### Credit Lifecycle Metrics

| KPI | Healthy Range | Why It Matters |
| --- | --- | --- |
| **Total Credits Outstanding** | Stable or growing slowly | Credits are in circulation; value held by players |
| **Redemption Rate** | 60-80% of issued | Players trust + use credits; not abandoning |
| **Avg Redemption Value** | ₹80-150 | Credits are used for real bookings, not just sitting |
| **Cost of Rewards (% of GMV)** | 2-5% | Sustainable; not cannibalizing margin |
| **Reward ROI** | 20-50x | For every ₹1 spent on rewards, gain ₹20-50 in LTV |

### Credit Allocation Strategy

```
Monthly Budget = GMV × 3% (e.g., ₹300 monthly GMV → ₹9 credits issued)

Distribution:
- 50% Match completion + slot-fill rewards
- 25% New player referrals (acquisition channel)
- 15% Off-peak incentives (capacity filling)
- 10% Team challenges + milestones
```

### Red Flags

| Signal | Problem | Action |
| --- | --- | --- |
| Redemption <40% | Credits not trusted | Investigate: prices? Redemption friction? |
| Outstanding >₹100k | Inflation risk | Pause new issuance; encourage redemption |
| Cost >10% of GMV | Unsustainable | Reduce reward tiers or tie more tightly to growth |
| Reward ROI <10x | Not generating growth | Are we rewarding existing players? Cut bloat. |

---

## 🤝 Team Network (`TeamNetworkMetric`)

### Network Growth

| KPI | Healthy Range | Why It Matters |
| --- | --- | --- |
| **Active Teams** | Growing 10-15% monthly | Community maturity |
| **Avg Team Size** | 6-8 players | Healthy team formation |
| **Team-vs-Team Matches** | 5-10% of all matches | Network deepening; not just booking |
| **Repeat Matchups** | >20% of team matches | Rivalry/relationships forming |
| **Challenge Acceptance Rate** | >40% | Team discovery is working |
| **Mature Teams (10+ matches)** | Growing 5-10% monthly | Retention of engaged teams |

### Team Profile Value

A mature team with 20+ completed matches has:
- **Stable revenue stream** (repeat booking behavior)
- **High LTV** (established members)
- **Peer recruitment potential** (new players ask to join)
- **Cross-promotion opportunity** (sponsor partnerships, tournaments)

---

## 👥 Referral System (`ReferralMetric`)

### Acquisition Efficiency

| KPI | Healthy Range | Why It Matters |
| --- | --- | --- |
| **Referral Rate** | >30% of new players | Word-of-mouth working |
| **Avg LTV (Referred Players)** | 1.5-2x higher than direct | Better retention |
| **Cost per Referral** | ₹30-50 credits | Cheaper than other channels |
| **Top Referrer Count** | 1 captain → 5-10 players | Identify advocates; create case studies |

### Referral Mechanics

**When Captain A brings Player B:**

1. Player B signs up with referral code
2. Player B plays their first match
3. **After match completion:** Captain A earns **₹40 credits**
4. No limit on number of referrals per captain

This encourages captains to **actively invite friends**, not just passively organize.

---

## ✅ Match Completion (`MatchCompletionMetric`)

### Quality Gates

| KPI | Healthy Range | Why It Matters |
| --- | --- | --- |
| **Completion Rate** | >85% | Matches are reliable; low no-show rate |
| **Dispute Rate** | <2% | Payment/logistics mostly working |
| **Avg Attendance** | >85% of booked slots | Actual engagement matches booking |
| **Reward Issued (Post-Complete)** | >90% of completed matches | Captain reward system is automated |

### Completion Workflow

```
1. Booking created
   ↓
2. Captain opens to community / players join
   ↓
3. Match day: Captain checks in via QR
   ↓
4. Players check in (mobile QR or manual)
   ↓
5. Match marked "completed" by system
   ↓
6. Wallet transactions finalized
   ↓
7. Captain rewards issued (if conditions met)
```

**Rewards are not issued until Step 5 is confirmed.** This prevents gaming.

---

## 👤 Player Engagement (`PlayerEngagementKPI`)

### Individual Metrics (Per Player)

| KPI | What to Watch | Action |
| --- | --- | --- |
| **Weekly Sessions** | <1 per week → at risk of churn | Send personalized "match nearby" notification |
| **Credits Outstanding** | High + redeemed rarely → investigate | Is redemption unclear? Offer coaching. |
| **Is Active Captain** | No → offer "host a match" onboarding | Captains have 3x LTV; convert casual → hosts |
| **Favorite Sport** | Emerging pattern → recommend leagues | Deepen single-sport engagement |
| **Players Referred** | >0 → power user → exclusive benefits | Early access to features, tournaments |

### Conversion Funnel

```
New Player (0 matches)
    ↓ Join as player
Casual Player (1-3 matches)
    ↓ Try hosting / invited to join a captain's team
Engaged Player (4+ matches in 30d)
    ↓ (15-20% convert)
Active Captain (2+ hosted matches in 30d)
    ↓ (5-10% convert)
Recurring Captain (4+ per month, recurring weekly)
```

**Target:** Move players down the funnel, especially casual → captain conversion.

---

## 📈 Venue Performance (Integrated into `VenueOverviewKPI`)

### Venue Health

| KPI | Healthy Range | Why It Matters |
| --- | --- | --- |
| **Avg Occupancy %** | >70% | Venue utilization good |
| **Matches with Teams** | >60% of bookings | Team/network effects active at venue |
| **Match Completion Rate** | >85% | Venue experience is good |
| **Repeat Captains** | >40% of bookings from repeat hosts | Venue is reliable; captains trust it |
| **Off-Peak Utilization** | Growing 10-15% | Incentives working |

### Venue Opportunity

A venue at 50% occupancy can reach 80-90% by:
1. **Off-peak incentives** (captain rewards for 6-10 AM, 10 PM bookings)
2. **Team network** (team-vs-team matches fill multiple courts simultaneously)
3. **Recurring matches** (weekly leagues, recurring captains reduce friction)

---

## 🔄 Community Growth Loop (System-Level)

The platform succeeds when:

```
1. Captain books a court (₹600)
2. Opens to community / invites friends
3. SportsOS notifies nearby players ("Match nearby!")
4. Players join
5. Match completes (QR check-in)
   ↓
6. Captain earns ₹20-30 credits ("Nice, I saved a little!")
7. New player brought earns ₹0 but positive experience
8. Established team gets notified: "Opponent team looking for match"
9. Teams challenge each other
10. Repeated matches form (rivalry)
11. More bookings → more GMV → more credit budget
12. Community network deepens
```

**Health indicators:**
- Step 1-2: GMV growing
- Step 3-4: Referral rate >30%, match fill rate >85%
- Step 5-6: Completion rate >85%, reward issued >90%
- Step 7-8: New player retention >60%
- Step 9-10: Team-vs-team matches growing 10%+ monthly
- Step 11-12: GMV growth + credits still <5% of GMV

---

## 📋 Monthly Reporting Checklist

### Week 1: Core Metrics
- [ ] DAU, MAU, active captains
- [ ] GMV, MRR, ARR
- [ ] New players, referral rate
- [ ] Player retention (7d, 30d)

### Week 2: Program Metrics
- [ ] Credits issued, redeemed, outstanding
- [ ] Reward cost % of GMV
- [ ] Captain reward ROI
- [ ] Match completion rate

### Week 3: Network Metrics
- [ ] Team count, active teams
- [ ] Team-vs-team matches
- [ ] Challenge acceptance rate
- [ ] Repeat matchup %

### Week 4: Diagnosis & Planning
- [ ] Identify 1-2 KPIs below range
- [ ] Root cause analysis
- [ ] Design intervention
- [ ] Set next month targets

---

## 🎯 Sample Monthly Dashboard

```
PLATFORM HEALTH

Engagement
├─ Monthly Active Users: 850 (↑12% WoW)
├─ Active Captains: 145 (↑8% WoW)
├─ Churn Rate: 12% (target: <15%)
└─ Retention 30d: 62% (target: >60%)

Revenue & Growth
├─ GMV: ₹125,000 (↑15% WoW)
├─ New Players: 95 (↑18% WoW)
├─ Organic Referral Rate: 35% (↑5pt)
└─ MRR: ₹8,500

Rewards Program
├─ Credits Issued: ₹3,250 (2.6% of GMV)
├─ Credits Redeemed: ₹2,100 (65% redemption)
├─ Avg Reward per Match: ₹22
└─ Reward ROI: 35x

Team Network
├─ Total Teams: 280 (↑15 this month)
├─ Team-vs-Team Matches: 18 (↑6 WoW)
├─ Challenge Acceptance: 42% (↑3pt)
└─ Mature Teams (10+): 34 (↑5)

Quality
├─ Match Completion: 87% (↑2pt)
├─ Dispute Rate: 1.2% (↓0.3pt)
└─ Referral LTV: 2.1x base
```

---

## 🚀 Using KPIs to Drive Product Decisions

### Example 1: Referral Rate Dropping

**KPI Alert:** Organic referral rate down to 25% (was 35%)

**Investigation:**
- Did new reward tiers launch? (Check creation_date)
- Are existing captains earning less? (Check avg_credits_per_match)
- Did app experience break? (Check match_completion_rate)

**Action:** If avg reward dropped → increase "new player" bonus from ₹30 to ₹50 (test for 2 weeks)

### Example 2: Completion Rate Low

**KPI Alert:** Match completion rate at 78% (target >85%)

**Hypothesis:** QR check-in is friction; players forget

**Action:** Send SMS reminder 30 mins before match: "Hey! Your badminton match starts soon. Make sure to check in with your captain's QR code."

### Example 3: Off-Peak Slots Empty

**KPI Alert:** 6-10 AM occupancy still at 35% vs target 70%

**Hypothesis:** Captains don't know about bonus rewards

**Action:** Homepage banner during booking: "☀️ Book 6-10 AM? Earn +₹20 extra credits!" + Email existing captains

---

## 🎓 Interpretation Guide

### When metrics conflict

**Example:** Referral rate down but new player LTV up

- **Don't:** Blindly chase referral rate
- **Do:** Understand why (maybe stricter referral approval = better quality players)
- **Action:** Track referred-player quality; if LTV 2x higher, keep the quality filter

### Healthy vs. Unhealthy Growth

| Pattern | Signal | Action |
| --- | --- | --- |
| GMV ↑ + Captains ↑ + Completion ↑ | Sustainable growth | Scale slowly; monitor unit economics |
| GMV ↑ + Captains ↓ + Rewards ↑ | Unsustainable (reward inflation) | Reduce reward tiers; focus on retention |
| GMV → Captains ↑ + Completion ↓ | Quality degrading | Investigate: new venues bad? App bugs? |
| Churn ↑ + Retention ↓ + Completion ↓ | Core experience broken | Priority: fix match completion, then re-engage |

---

## 📞 When to Alert Leadership

| Condition | Impact | Action |
| --- | --- | --- |
| Churn >20% for 2 weeks | Losing users fast | Debug match quality / refund issues |
| Reward cost >8% for 2 months | Margin erosion | Audit reward tiers; cut bloat |
| Completion <75% for 2 weeks | Experience broken | Investigate QR check-in, payment friction |
| Referral rate <20% | Growth stalled | Diagnosis; may need product pivot |
| GMV growth <2% for 2 months | Traction loss | Review: pricing, marketing, UI/UX |

---

## 🏁 Success Criteria (6-Month Vision)

```
Month 6 Target:

├─ Monthly Active Users: 2,500+
├─ Active Captains: 400+ (16% of users)
├─ GMV: ₹500,000+
├─ Organic Referral Rate: >40%
├─ Match Completion: >90%
├─ Credits Cost: 2-3% of GMV
├─ Team-vs-Team Matches: 100+/month
├─ Churn Rate: <10%
└─ Reward ROI: 25-40x
```

If achieved → sustainable business model with strong community network effects.
