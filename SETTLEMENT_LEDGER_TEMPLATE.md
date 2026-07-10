# 📊 SportsOS Settlement Ledger

**Purpose:** Track all payments collected and paid to venue owners weekly

---

## Weekly Settlement Report Template

**Report Period:** [Start Date] – [End Date]  
**Venue:** [Venue Name]  
**Venue ID:** [tenant_id]  
**Venue Owner:** [Name]  
**Payout Date:** [Monday of next week]  

---

### Collections

| Date | Player | Sport | Court | Time | Duration | Rate | Amount |
|------|--------|-------|-------|------|----------|------|--------|
| Jul 9 | Arjun | Badminton | 1 | 6:00 PM | 1 hr | ₹600 | ₹600 |
| Jul 9 | Priya | Badminton | 1 | 6:00 PM | 1 hr | ₹600 | ₹600 |
| Jul 9 | Rahul | Badminton | 1 | 6:00 PM | 1 hr | ₹600 | ₹600 |
| Jul 10 | Arjun | Cricket | 2 | 7:00 PM | 2 hr | ₹800 | ₹1,600 |

**Total Collected:** ₹3,400

---

### Deductions

| Type | Amount | Reason |
|------|--------|--------|
| Refunds | ₹0 | — |
| Platform Fee (1%) | ₹34 | Processing fee |
| **Total Deductions** | **₹34** | |

---

### Net Payout

```
Total Collected      ₹3,400
Less: Refunds        ₹0
Less: Platform Fee   ₹34
─────────────────────────
Net Due              ₹3,366
```

---

### Payment Method

**Bank Transfer**

| Field | Value |
|-------|-------|
| Venue Name | ABC Sports Arena |
| Account Holder | [Owner Name] |
| Bank Name | [Bank] |
| Account Number | [XXXXXX] |
| IFSC | [IFSC Code] |
| Amount | ₹3,366 |
| Reference | Settlement-ABC-Jul9-15 |

---

### Confirmation

```
Payout Date:     July 15, 2026
Status:          ✅ Paid
Receipt Number:  PAY-ABC-20260715-001
UTR/Ref ID:      [Transaction ID]
```

---

## Monthly Summary (Tracking)

Keep this updated weekly as settlements happen:

| Week | Period | Venue | Amount | Status | Notes |
|------|--------|-------|--------|--------|-------|
| 1 | Jul 9–15 | ABC Arena | ₹3,366 | ✅ Paid | — |
| 2 | Jul 16–22 | ABC Arena | ₹4,200 | ✅ Paid | — |
| 3 | Jul 23–29 | ABC Arena | ₹5,100 | ⏳ Pending | Payout 7/29 |
| 4 | Jul 30–Aug 5 | ABC Arena | ₹6,800 | — | — |

**Monthly Total (July):** ₹19,466

---

## Venue Owner Communications

### Settlement Email Template

**Subject:** Weekly Settlement — ABC Sports Arena (Jul 9–15)

---

Dear [Venue Owner Name],

Your weekly settlement for **ABC Sports Arena** is ready.

**Period:** July 9–15, 2026

| Metric | Value |
|--------|-------|
| Total Collections | ₹3,400 |
| Bookings | 4 |
| Avg per booking | ₹850 |
| Refunds | ₹0 |
| Platform Fee (1%) | ₹34 |
| **Net Settlement** | **₹3,366** |

**Payment Details:**
- Method: Bank Transfer
- Amount: ₹3,366
- Expected Receipt: July 15, 2026 EOD

**Next Settlement:** July 22, 2026

---

Questions? Reply to this email or check your dashboard at http://localhost:8501

Thanks for being part of SportsOS!

**— SportsOS Team**

---

## Bookkeeping Records (Keep for Tax/Audit)

### Income Statement (Monthly Example)

```
SportsOS - July 2026 P&L

REVENUE
  Booking Collections        ₹19,466
  Platform Fees (1%)            ₹194
  ─────────────────────────────────
  Gross Revenue             ₹19,660

COSTS
  Payment Settlements       (₹19,466)
  ─────────────────────────────────
  Net Margin                    ₹194

Note: This excludes operational costs (servers, staff, etc.)
```

### Cash Flow (Track Timing)

```
Monday (Bookings collected Tue-Mon)
    ↓
Tuesday (Final collections)
    ↓
Wednesday (Prepare settlement)
    ↓
Thursday (Approval)
    ↓
Friday (Bank wire initiated)
    ↓
Monday (Funds arrive in venue account)
```

---

## Scaling Checklist

- [ ] Week 1–4: Manual Excel tracking (this template)
- [ ] Week 5: Move to Google Sheets with formulas
- [ ] Month 2: Integrate settlement dashboard in Streamlit
- [ ] Month 3: Automated weekly settlements (via Razorpay API)
- [ ] Month 6: Full accounting system (QuickBooks/Tally)

---

## Venue Owner Retention

Send weekly settlements to maintain trust:

✅ **Every Monday** at 9 AM:
1. Send settlement report (email + Streamlit dashboard)
2. Confirm bank wire initiated
3. Ask: "How can we improve?"

This builds confidence that SportsOS is reliable and transparent.

---

**Keep all settlement records for 7 years for tax/compliance.**
