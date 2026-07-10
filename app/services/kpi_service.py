"""KPI and analytics calculation service."""

from datetime import date, datetime, timedelta
from typing import Any

from fastapi import HTTPException

from app.core.db import Client, FieldFilter
from app.models.kpi import (
    CaptainRewardMetric,
    CreditsMetric,
    CustomerMetric,
    MatchCompletionMetric,
    MatchmakingMetric,
    OccupancyMetric,
    PlayerEngagementKPI,
    PlayerKPIScope,
    PlatformAdminKPI,
    ReferralMetric,
    RevenueMetric,
    TeamMetric,
    TeamNetworkMetric,
    VenueKPIScope,
    VenueOverviewKPI,
)


def get_venue_overview_kpi(
    db: Any, tenant_id: str, scope: VenueKPIScope = VenueKPIScope.TODAY
) -> VenueOverviewKPI:
    """Calculate daily venue KPIs: revenue, occupancy, customers, matchmaking."""
    if scope == VenueKPIScope.TODAY:
        period_start = date.today()
        period_end = date.today()
    elif scope == VenueKPIScope.WEEK:
        today = date.today()
        period_start = today - timedelta(days=today.weekday())
        period_end = today
    elif scope == VenueKPIScope.MONTH:
        today = date.today()
        period_start = date(today.year, today.month, 1)
        period_end = today
    else:
        raise ValueError(f"Unknown scope: {scope}")

    # --- Revenue: sum all confirmed bookings in period, group by wallet transactions ---
    revenue_amount = 0.0
    transaction_count = 0
    bookings_iter = (
        db.collection("tenants").document(tenant_id).collection("bookings")
        .where(filter=FieldFilter("date", ">=", period_start.isoformat()))
        .where(filter=FieldFilter("date", "<=", period_end.isoformat()))
        .where(filter=FieldFilter("status", "==", "confirmed"))
        .stream()
    )
    for booking_doc in bookings_iter:
        booking = booking_doc.to_dict()
        revenue_amount += booking.get("price", 0.0)
        transaction_count += 1

    avg_transaction = revenue_amount / transaction_count if transaction_count > 0 else 0.0

    # --- Occupancy: per-court utilization ---
    occupancy_list = []
    courts_iter = db.collection("tenants").document(tenant_id).collection("courts").stream()
    for court_doc in courts_iter:
        court_id = court_doc.id
        court_data = court_doc.to_dict()
        court_name = court_data.get("name", "?")
        sport = court_data.get("sport", "?")

        # Count booked and available hours in period
        booked_hours = 0.0
        bookings_count = 0
        no_shows = 0
        cancellations = 0

        court_bookings = (
            db.collection("tenants").document(tenant_id).collection("bookings")
            .where(filter=FieldFilter("court_id", "==", court_id))
            .where(filter=FieldFilter("date", ">=", period_start.isoformat()))
            .where(filter=FieldFilter("date", "<=", period_end.isoformat()))
            .stream()
        )
        for booking_doc in court_bookings:
            b = booking_doc.to_dict()
            if b.get("status") == "confirmed":
                bookings_count += 1
                booked_hours += (int(b.get("end_time", "00:00").split(":")[0]) -
                                 int(b.get("start_time", "00:00").split(":")[0]))
            elif b.get("status") == "cancelled":
                cancellations += 1
            elif b.get("status") == "no_show":
                no_shows += 1

        # Available hours = (close_time - open_time) * days in period
        open_h = int(court_data.get("open_time", "00:00").split(":")[0])
        close_h = int(court_data.get("close_time", "23:00").split(":")[0])
        daily_hours = close_h - open_h
        days_in_period = (period_end - period_start).days + 1
        available_hours = daily_hours * days_in_period

        utilization_pct = (booked_hours / available_hours * 100) if available_hours > 0 else 0.0

        occupancy_list.append(
            OccupancyMetric(
                court_id=court_id,
                court_name=court_name,
                sport=sport,
                utilization_percent=round(utilization_pct, 2),
                booked_hours=booked_hours,
                available_hours=available_hours,
                bookings_count=bookings_count,
                no_show_count=no_shows,
                cancelled_count=cancellations,
            )
        )

    avg_occupancy = (
        sum(o.utilization_percent for o in occupancy_list) / len(occupancy_list)
        if occupancy_list
        else 0.0
    )

    # --- Customers: unique players, repeats, churn ---
    player_booking_counts = {}
    new_players = set()
    for booking_doc in db.collection("tenants").document(tenant_id).collection("bookings").where(
        filter=FieldFilter("status", "==", "confirmed")
    ).stream():
        b = booking_doc.to_dict()
        created_by = b.get("created_by")
        if created_by:
            player_booking_counts[created_by] = player_booking_counts.get(created_by, 0) + 1
            # Check if this is their first booking ever (approximated as period_start)
            b_date = b.get("date", "")
            if b_date == period_start.isoformat():
                new_players.add(created_by)

    # Count repeats from participants (players who joined, not captains)
    for booking_doc in db.collection("tenants").document(tenant_id).collection("bookings").where(
        filter=FieldFilter("status", "==", "confirmed")
    ).stream():
        for participant_doc in booking_doc.reference.collection("participants").stream():
            p = participant_doc.to_dict()
            uid = p.get("uid")
            if uid:
                player_booking_counts[uid] = player_booking_counts.get(uid, 0) + 1

    active_players = len(player_booking_counts)
    returning = sum(1 for count in player_booking_counts.values() if count >= 2)
    repeat_pct = (returning / active_players * 100) if active_players > 0 else 0.0

    # Approximate LTV: total revenue / active players
    ltv = revenue_amount / active_players if active_players > 0 else 0.0

    customers = CustomerMetric(
        active_customers=active_players,
        new_customers=len(new_players),
        returning_customers=returning,
        repeat_booking_percent=round(repeat_pct, 2),
        avg_lifetime_value=round(ltv, 2),
    )

    # --- Matchmaking: Join Match queue metrics ---
    total_queued = 0
    matches_formed = 0
    queued_uids = set()
    matched_uids = set()
    cancellations = 0

    match_reqs = db.collection("tenants").document(tenant_id).collection("match_requests").where(
        filter=FieldFilter("created_at", ">=", f"{period_start}T00:00:00Z")
    ).stream()
    for req_doc in match_reqs:
        req = req_doc.to_dict()
        status = req.get("status")
        uid = req.get("uid")
        if uid:
            queued_uids.add(uid)
        if status == "waiting":
            total_queued += 1
        elif status == "matched":
            matches_formed += 1
            if uid:
                matched_uids.add(uid)
        elif status == "cancelled":
            cancellations += 1

    match_fill_rate = (len(matched_uids) / len(queued_uids) * 100) if queued_uids else 0.0
    cancel_rate = (cancellations / (len(queued_uids) + cancellations) * 100) if (queued_uids or cancellations) else 0.0

    matchmaking = MatchmakingMetric(
        total_queued=len(queued_uids),
        matches_formed=matches_formed,
        match_fill_rate=round(match_fill_rate, 2),
        avg_fill_time_seconds=0.0,  # TODO: calculate from created_at to matched_at timestamps
        queue_cancellations=cancellations,
        cancellation_rate=round(cancel_rate, 2),
    )

    # --- Teams formed from bookings at this venue in period ---
    team_ids_at_venue = set()
    completed_team_ids = set()
    for booking_doc in db.collection("tenants").document(tenant_id).collection("bookings").stream():
        b = booking_doc.to_dict()
        b_date = b.get("date", "")
        team_id = b.get("team_id")
        if team_id and period_start.isoformat() <= b_date <= period_end.isoformat():
            team_ids_at_venue.add(team_id)
            if b.get("status") == "completed":
                completed_team_ids.add(team_id)

    total_team_participants = sum(
        len(list(db.collection("teams").document(team_id).collection("members").stream()))
        for team_id in team_ids_at_venue
    )
    avg_team_size = (total_team_participants / len(team_ids_at_venue)) if team_ids_at_venue else 0.0

    teams_metric = TeamMetric(
        teams_formed=len(team_ids_at_venue),
        avg_team_size=round(avg_team_size, 2),
        total_team_participants=total_team_participants,
        teams_completed=len(completed_team_ids),
    )

    # --- Match completion / quality (dispute tracking not implemented yet, so those stay 0) ---
    from app.services import rewards_service

    matches_created_count = 0
    matches_completed_count = 0
    no_show_count_total = 0
    attendance_ratios = []
    reward_issued_after_completion = 0
    for booking_doc in db.collection("tenants").document(tenant_id).collection("bookings").stream():
        b = booking_doc.to_dict()
        b_date = b.get("date", "")
        if not (period_start.isoformat() <= b_date <= period_end.isoformat()):
            continue
        matches_created_count += 1
        b_status = b.get("status")
        if b_status == "completed":
            matches_completed_count += 1
            slots_total = b.get("slots_total") or 0
            if slots_total:
                checkins = list(booking_doc.reference.collection("checkins").stream())
                attendance_ratios.append(min(len(checkins) / slots_total, 1.0))
            captain_uid = b.get("created_by")
            if captain_uid and any(
                r.get("related_booking_id") == booking_doc.id and r.get("reward_type") == "match_completed"
                for r in rewards_service.list_player_rewards(db, captain_uid)
            ):
                reward_issued_after_completion += 1
        elif b_status == "no_show":
            no_show_count_total += 1

    completion_rate = (matches_completed_count / matches_created_count * 100) if matches_created_count else 0.0
    no_show_rate = (no_show_count_total / matches_created_count * 100) if matches_created_count else 0.0
    avg_attendance = (sum(attendance_ratios) / len(attendance_ratios) * 100) if attendance_ratios else 0.0

    match_completion = MatchCompletionMetric(
        period_start=period_start,
        period_end=period_end,
        matches_created=matches_created_count,
        matches_completed=matches_completed_count,
        completion_rate=round(completion_rate, 2),
        no_show_rate=round(no_show_rate, 2),
        avg_actual_attendance=round(avg_attendance, 2),
        matches_with_disputes=0,
        dispute_rate=0.0,
        reward_issued_after_completion=reward_issued_after_completion,
    )

    # --- Fetch venue name ---
    venue_doc = db.collection("tenants").document(tenant_id).get()
    venue_name = venue_doc.to_dict().get("name", "?") if venue_doc.exists else "?"

    return VenueOverviewKPI(
        venue_name=venue_name,
        scope=scope,
        period_start=period_start,
        period_end=period_end,
        revenue=RevenueMetric(
            total_revenue=round(revenue_amount, 2),
            transaction_count=transaction_count,
            avg_transaction_value=round(avg_transaction, 2),
            recurring_revenue=0.0,  # TODO: memberships/subscriptions
            transaction_revenue=revenue_amount,
        ),
        occupancy=occupancy_list,
        customers=customers,
        teams=teams_metric,
        matchmaking=matchmaking,
        match_completion=match_completion,
        avg_occupancy_percent=round(avg_occupancy, 2),
    )


def get_player_engagement_kpi(
    db: Any, uid: str, scope: PlayerKPIScope = PlayerKPIScope.MONTH
) -> PlayerEngagementKPI:
    """Player north-star metrics: matches, hours, spending, retention."""
    if scope == PlayerKPIScope.MONTH:
        period_start = date.today().replace(day=1)
        period_end = date.today()
    elif scope == PlayerKPIScope.QUARTER:
        today = date.today()
        quarter_start_month = ((today.month - 1) // 3) * 3 + 1
        period_start = date(today.year, quarter_start_month, 1)
        period_end = today
    elif scope == PlayerKPIScope.YEAR:
        today = date.today()
        period_start = date(today.year, 1, 1)
        period_end = today
    else:
        period_start = date(1970, 1, 1)
        period_end = date(2100, 12, 31)

    # --- Get player profile ---
    user_doc = db.collection("users").document(uid).get()
    user_data = user_doc.to_dict() if user_doc.exists else {}
    display_name = user_data.get("display_name", uid)

    # --- Find all bookings where this player was involved (captain or participant) ---
    matches_played = 0
    courts_booked = 0
    total_hours = 0.0
    booking_dates = set()
    total_spend = 0.0
    sports_played = {}
    venues_visited = set()

    # Bookings created by this player (captain role)
    for tenant_doc in db.collection("tenants").stream():
        tenant_id = tenant_doc.id
        for booking_doc in (
            db.collection("tenants").document(tenant_id).collection("bookings")
            .where(filter=FieldFilter("created_by", "==", uid))
            .where(filter=FieldFilter("status", "==", "confirmed"))
            .stream()
        ):
            b = booking_doc.to_dict()
            b_date = b.get("date")
            if period_start.isoformat() <= b_date <= period_end.isoformat():
                courts_booked += 1
                start_h = int(b.get("start_time", "00:00").split(":")[0])
                end_h = int(b.get("end_time", "23:00").split(":")[0])
                total_hours += (end_h - start_h)
                booking_dates.add(b_date)
                sport = b.get("sport", "unknown")
                sports_played[sport] = sports_played.get(sport, 0) + 1
                venues_visited.add(tenant_id)
                # Find cost split among participants
                participant_count = 1 + len(list(booking_doc.reference.collection("participants").stream()))
                total_spend += b.get("price", 0.0) / participant_count

        # Bookings where this player joined (participant)
        for booking_doc in db.collection("tenants").document(tenant_id).collection("bookings").where(
            filter=FieldFilter("status", "==", "confirmed")
        ).stream():
            for participant_doc in booking_doc.reference.collection("participants").stream():
                p = participant_doc.to_dict()
                if p.get("uid") == uid:
                    matches_played += 1
                    b = booking_doc.to_dict()
                    b_date = b.get("date")
                    if period_start.isoformat() <= b_date <= period_end.isoformat():
                        start_h = int(b.get("start_time", "00:00").split(":")[0])
                        end_h = int(b.get("end_time", "23:00").split(":")[0])
                        total_hours += (end_h - start_h)
                        booking_dates.add(b_date)
                        sport = b.get("sport", "unknown")
                        sports_played[sport] = sports_played.get(sport, 0) + 1
                        venues_visited.add(tenant_id)
                        # Cost is split among all participants
                        participant_count = 1 + len(list(booking_doc.reference.collection("participants").stream()))
                        total_spend += b.get("price", 0.0) / participant_count

    weekly_sessions = len(booking_dates) / ((period_end - period_start).days / 7.0) if booking_dates else 0.0
    favorite_sport = max(sports_played, key=sports_played.get) if sports_played else None

    # --- Wallet balance and all-time bookings ---
    wallet_doc = db.collection("players").document(uid).collection("wallet").document("wallet").get()
    wallet_balance = wallet_doc.to_dict().get("balance", 0.0) if wallet_doc.exists else 0.0

    # Count total active bookings
    bookings_this_period = 0
    for tenant_doc in db.collection("tenants").stream():
        tenant_id = tenant_doc.id
        bookings_this_period += len(
            list(
                db.collection("tenants").document(tenant_id).collection("bookings")
                .where(filter=FieldFilter("created_by", "==", uid))
                .where(filter=FieldFilter("status", "in", ["confirmed", "waiting"]))
                .where(filter=FieldFilter("date", ">=", period_start.isoformat()))
                .stream()
            )
        )

    favorite_venue = None
    if venues_visited:
        venue_counts = {}
        for venue_id in venues_visited:
            venue_doc = db.collection("tenants").document(venue_id).get()
            venue_counts[venue_id] = venue_doc.to_dict().get("name") if venue_doc.exists else "?"
        favorite_venue = venue_counts.get(max(venues_visited, key=lambda v: list(venues_visited).count(v)))

    # --- Teams captained/joined in period ---
    teams_captained = 0
    teams_joined = 0
    for team_doc in db.collection("teams").stream():
        team_data = team_doc.to_dict()
        if period_start.isoformat() <= team_data.get("created_at", "")[:10] <= period_end.isoformat():
            if team_data.get("captain_uid") == uid:
                teams_captained += 1
            elif team_doc.reference.collection("members").document(uid).get().exists:
                teams_joined += 1

    # --- Credits earned/referred in period (avoid a hard import cycle with rewards_service) ---
    from app.services import rewards_service

    rewards = rewards_service.list_player_rewards(db, uid)
    credits_earned = round(
        sum(
            r.get("credits_amount", 0.0)
            for r in rewards
            if period_start.isoformat() <= r.get("issued_at", "")[:10] <= period_end.isoformat()
        ),
        2,
    )
    referrals = rewards_service.list_player_referrals(db, uid)
    players_referred = sum(
        1
        for r in referrals
        if period_start.isoformat() <= r.get("referred_at", "")[:10] <= period_end.isoformat()
    )

    # Single unified wallet ledger today (no separate cash/credits split), so
    # credits redeemed/outstanding are read off the same debit total and balance.
    credits_redeemed = round(total_spend, 2)
    credits_outstanding = round(wallet_balance, 2)

    is_captain = teams_captained > 0
    is_active_captain = teams_captained >= 2

    return PlayerEngagementKPI(
        uid=uid,
        display_name=display_name,
        scope=scope,
        period_start=period_start,
        period_end=period_end,
        matches_played=matches_played,
        teams_captained=teams_captained,
        teams_joined=teams_joined,
        courts_booked=courts_booked,
        hours_played=round(total_hours, 1),
        bookings_this_period=bookings_this_period,
        wallet_total_spend=round(total_spend, 2),
        wallet_balance=round(wallet_balance, 2),
        credits_earned=credits_earned,
        credits_redeemed=credits_redeemed,
        credits_outstanding=credits_outstanding,
        weekly_sessions=round(weekly_sessions, 2),
        favorite_venue=favorite_venue,
        favorite_sport=favorite_sport,
        repeat_venues=len(venues_visited),
        players_referred=players_referred,
        is_captain=is_captain,
        is_active_captain=is_active_captain,
    )


def get_platform_admin_kpi(db: Any) -> PlatformAdminKPI:
    """System-wide health: DAU, MAU, GMV, churn, retention."""
    today = date.today()
    month_ago = today - timedelta(days=30)
    week_ago = today - timedelta(days=7)

    # --- Count active venues and players ---
    total_venues = len(list(db.collection("tenants").stream()))
    total_players = len(list(db.collection("users").where(filter=FieldFilter("roles.player", "==", True)).stream()))

    active_venues_set = set()
    active_players_today = set()
    active_players_month = set()
    active_players_week_ago = set()
    active_captains_month = set()
    active_team_ids_month = set()

    for tenant_doc in db.collection("tenants").stream():
        tenant_id = tenant_doc.id
        # Check for recent bookings
        recent_bookings = list(
            db.collection("tenants").document(tenant_id).collection("bookings").where(
                filter=FieldFilter("date", ">=", month_ago.isoformat())
            ).stream()
        )
        if recent_bookings:
            active_venues_set.add(tenant_id)
            for b_doc in recent_bookings:
                b = b_doc.to_dict()
                b_date = b.get("date")
                if b_date == today.isoformat():
                    active_players_today.add(b.get("created_by"))
                if b_date >= month_ago.isoformat():
                    active_players_month.add(b.get("created_by"))
                    active_captains_month.add(b.get("created_by"))
                    if b.get("team_id"):
                        active_team_ids_month.add(b["team_id"])
                if b_date == (week_ago).isoformat():
                    active_players_week_ago.add(b.get("created_by"))
                # Participants
                for p_doc in b_doc.reference.collection("participants").stream():
                    p = p_doc.to_dict()
                    if b_date == today.isoformat():
                        active_players_today.add(p.get("uid"))
                    if b_date >= month_ago.isoformat():
                        active_players_month.add(p.get("uid"))
                    if b_date == (week_ago).isoformat():
                        active_players_week_ago.add(p.get("uid"))

    active_venues = len(active_venues_set)
    dau = len(active_players_today)
    mau = len(active_players_month)
    active_captains = len(active_captains_month)

    # --- Counts: bookings, matches formed ---
    bookings_today = 0
    bookings_month = 0
    matches_formed_today = 0
    matches_formed_month = 0
    gmv_today = 0.0
    gmv_month = 0.0

    for tenant_doc in db.collection("tenants").stream():
        tenant_id = tenant_doc.id
        for b_doc in db.collection("tenants").document(tenant_id).collection("bookings").where(
            filter=FieldFilter("status", "==", "confirmed")
        ).stream():
            b = b_doc.to_dict()
            b_date = b.get("date")
            price = b.get("price", 0.0)
            if b_date == today.isoformat():
                bookings_today += 1
                gmv_today += price
            if b_date >= month_ago.isoformat():
                bookings_month += 1
                gmv_month += price

        # Match formations (Join Match queue)
        for req_doc in db.collection("tenants").document(tenant_id).collection("match_requests").stream():
            req = req_doc.to_dict()
            if req.get("status") == "matched":
                created_ts = req.get("created_at", "")
                if created_ts.startswith(today.isoformat()):
                    matches_formed_today += 1
                if created_ts >= f"{month_ago}T00:00:00":
                    matches_formed_month += 1

    # --- Payment success rate and MRR/ARR ---
    payment_success_rate = 95.0  # TODO: track actual failed transactions
    mrr = gmv_month / 12 if gmv_month > 0 else 0.0  # Rough estimate
    arr = mrr * 12

    # --- Retention: % of month-old players still active this month ---
    retention_7d = (len(active_players_week_ago & active_players_month) / len(active_players_week_ago) * 100) if active_players_week_ago else 0.0
    retention_30d = 0.0  # Would need historical snapshot from 30 days ago
    captain_retention_30d = 0.0  # Would need historical snapshot from 30 days ago

    # --- Match completion (all statuses, platform-wide, this month) ---
    matches_created_month = 0
    matches_completed_month = 0
    for tenant_doc in db.collection("tenants").stream():
        tenant_id = tenant_doc.id
        for b_doc in db.collection("tenants").document(tenant_id).collection("bookings").stream():
            b = b_doc.to_dict()
            b_date = b.get("date", "")
            if b_date >= month_ago.isoformat():
                matches_created_month += 1
                if b.get("status") == "completed":
                    matches_completed_month += 1
    match_completion_rate = (matches_completed_month / matches_created_month * 100) if matches_created_month else 0.0
    match_dispute_rate = 0.0  # No dispute tracking implemented yet

    # --- Teams & team-vs-team challenges (platform-wide) ---
    total_teams = len(list(db.collection("teams").stream()))
    active_teams = len(active_team_ids_month)

    challenges = list(db.collection("team_challenges").stream())
    accepted_challenges = [c for c in challenges if c.to_dict().get("status") == "accepted"]
    accepted_challenges_month = [
        c for c in accepted_challenges if c.to_dict().get("accepted_at", "") >= month_ago.isoformat()
    ]
    team_vs_team_matches_month = len(accepted_challenges_month)
    team_vs_team_acceptance_rate = (len(accepted_challenges) / len(challenges) * 100) if challenges else 0.0

    # --- Credits issued/redeemed this month (reuse the credits metric, same month-to-date window) ---
    credits_metric = get_credits_metric(db)
    credits_issued_this_month = credits_metric.total_credits_issued
    credits_redeemed_this_month = credits_metric.total_credits_redeemed
    reward_cost_percent = (credits_issued_this_month / gmv_month * 100) if gmv_month > 0 else 0.0

    # --- New players & referrals this month ---
    new_players_this_month = sum(
        1
        for doc in db.collection("users").stream()
        if doc.to_dict().get("created_at", "") >= f"{month_ago.isoformat()}T00:00:00"
    )
    new_players_from_referrals = sum(
        1
        for doc in db.collection_group("referrals").stream()
        if doc.to_dict().get("referred_at", "") >= f"{month_ago.isoformat()}T00:00:00"
    )
    organic_referral_rate = (
        (new_players_from_referrals / new_players_this_month * 100) if new_players_this_month else 0.0
    )

    return PlatformAdminKPI(
        snapshot_date=datetime.now(),
        active_venues=active_venues,
        total_venues=total_venues,
        active_players=mau,
        total_players=total_players,
        active_captains=active_captains,
        daily_active_users=dau,
        monthly_active_users=mau,
        bookings_today=bookings_today,
        bookings_this_month=bookings_month,
        matches_formed_today=matches_formed_today,
        matches_formed_this_month=matches_formed_month,
        team_vs_team_matches_month=team_vs_team_matches_month,
        gmv_today=round(gmv_today, 2),
        gmv_this_month=round(gmv_month, 2),
        mrr=round(mrr, 2),
        arr=round(arr, 2),
        credits_issued_this_month=round(credits_issued_this_month, 2),
        credits_redeemed_this_month=round(credits_redeemed_this_month, 2),
        reward_cost_percent=round(reward_cost_percent, 2),
        total_teams=total_teams,
        active_teams=active_teams,
        team_vs_team_acceptance_rate=round(team_vs_team_acceptance_rate, 2),
        new_players_this_month=new_players_this_month,
        new_players_from_referrals=new_players_from_referrals,
        organic_referral_rate=round(organic_referral_rate, 2),
        payment_success_rate=payment_success_rate,
        match_completion_rate=round(match_completion_rate, 2),
        match_dispute_rate=match_dispute_rate,
        player_retention_7d=round(retention_7d, 2),
        player_retention_30d=retention_30d,
        captain_retention_30d=captain_retention_30d,
        churn_rate=0.0,  # TODO: track historical active set
    )


def get_credits_metric(db: Client) -> CreditsMetric:
    """Calculate SportsOS Credits system metrics."""
    from datetime import date
    from app.models.kpi import CreditsMetric

    period_start = date.today().replace(day=1)
    period_end = date.today()

    # Get all rewards issued this month
    total_issued = 0.0
    total_redeemed = 0.0

    for user_doc in db.collection("users").stream():
        uid = user_doc.id
        rewards_collection = db.collection("players").document(uid).collection("rewards")
        for reward_doc in rewards_collection.stream():
            reward_data = reward_doc.to_dict()
            issued_date = reward_data.get("issued_at", "")
            if period_start.isoformat() <= issued_date[:10] <= period_end.isoformat():
                total_issued += reward_data.get("credits_amount", 0)

    # Get total outstanding credits (in wallets)
    total_outstanding = 0.0
    for user_doc in db.collection("players").stream():
        wallet_ref = db.collection("players").document(user_doc.id).collection("wallet").document("wallet")
        if wallet_ref.get().exists:
            wallet_data = wallet_ref.get().to_dict()
            total_outstanding += wallet_data.get("balance", 0)

    # Approximate: wallet balance mixes reward credits with peer-to-peer Join
    # Match/Hybrid Booking transfers, so this can't be exact without splitting
    # the ledger by money origin. Clamp so it can't go negative.
    total_redeemed = max(0.0, total_issued - total_outstanding)

    redemption_rate = (
        (total_redeemed / total_issued * 100) if total_issued > 0 else 0
    )

    # Get GMV for ROI calculation
    gmv_month = 0.0
    for doc in db.collection_group("bookings").stream():
        booking_data = doc.to_dict()
        if booking_data.get("status") == "completed":
            gmv_month += booking_data.get("price", 0)

    cost_of_rewards = (total_issued / gmv_month * 100) if gmv_month > 0 else 0
    reward_roi = (gmv_month / total_issued) if total_issued > 0 else 0

    return CreditsMetric(
        period_start=period_start,
        period_end=period_end,
        total_credits_issued=round(total_issued, 2),
        total_credits_redeemed=round(total_redeemed, 2),
        total_credits_outstanding=round(total_outstanding, 2),
        redemption_rate=round(redemption_rate, 2),
        avg_credits_per_captain=0.0,  # TODO: calculate
        avg_redemption_value=0.0,  # TODO: calculate
        cost_of_rewards=round(cost_of_rewards, 2),
        reward_roi=round(reward_roi, 2),
    )


def get_team_network_metric(db: Client) -> TeamNetworkMetric:
    """Calculate team network growth metrics."""
    from datetime import date
    from app.models.kpi import TeamNetworkMetric

    period_start = date.today().replace(day=1)
    period_end = date.today()

    teams = list(db.collection("teams").stream())
    active_teams = [t for t in teams if t.to_dict().get("status") == "active"]
    new_teams = [t for t in teams if period_start.isoformat() <= t.to_dict().get("created_at", "")[:10] <= period_end.isoformat()]

    # Calculate team-vs-team matches
    team_vs_team_matches = len(
        list(db.collection("team_challenges").where(
            filter=FieldFilter("status", "==", "accepted")
        ).stream())
    )

    # Calculate average team size
    avg_team_size = 0.0
    if active_teams:
        total_members = 0
        for team_doc in active_teams:
            team_id = team_doc.id
            members = list(db.collection("teams").document(team_id).collection("members").stream())
            total_members += len(members)
        avg_team_size = total_members / len(active_teams)

    # Challenge acceptance rate
    all_challenges = list(db.collection("team_challenges").stream())
    accepted_challenges = [c for c in all_challenges if c.to_dict().get("status") == "accepted"]
    challenge_acceptance_rate = (
        (len(accepted_challenges) / len(all_challenges) * 100) if all_challenges else 0
    )

    return TeamNetworkMetric(
        period_start=period_start,
        period_end=period_end,
        teams_active=len(active_teams),
        new_teams=len(new_teams),
        team_vs_team_matches=team_vs_team_matches,
        avg_team_size=round(avg_team_size, 1),
        avg_team_rating=0.0,  # TODO: implement team ratings
        teams_with_10_plus_matches=0,  # TODO: track match counts per team
        friendly_challenge_count=len(all_challenges),
        challenge_acceptance_rate=round(challenge_acceptance_rate, 2),
        repeat_matchups=0,  # TODO: track repeat team matchups
    )


def get_referral_metric(db: Client) -> ReferralMetric:
    """Calculate referral acquisition metrics."""
    from datetime import date
    from app.models.kpi import ReferralMetric

    period_start = date.today().replace(day=1)
    period_end = date.today()

    # Count total new players
    new_players_total = 0
    new_players_from_referrals = 0

    for user_doc in db.collection("users").stream():
        user_data = user_doc.to_dict()
        created_date = user_data.get("created_at", "")[:10]
        if period_start.isoformat() <= created_date <= period_end.isoformat():
            new_players_total += 1
            # Check if referred (TODO: implement proper referral tracking)

    referral_rate = (
        (new_players_from_referrals / new_players_total * 100) if new_players_total > 0 else 0
    )

    return ReferralMetric(
        period_start=period_start,
        period_end=period_end,
        new_players_total=new_players_total,
        new_players_from_referrals=new_players_from_referrals,
        referral_rate=round(referral_rate, 2),
        avg_lifetime_value_referred=0.0,  # TODO: track LTV by cohort
        top_referrer_uid=None,
        top_referrer_count=0,
        referral_credit_cost=0.0,  # TODO: sum referral rewards issued
    )


def get_match_completion_metric(db: Client) -> MatchCompletionMetric:
    """Calculate match quality and completion metrics."""
    from datetime import date
    from app.models.kpi import MatchCompletionMetric

    period_start = date.today().replace(day=1)
    period_end = date.today()

    matches_created = 0
    matches_completed = 0
    matches_with_disputes = 0

    for doc in db.collection_group("bookings").stream():
        booking_data = doc.to_dict()
        created_date = booking_data.get("created_at", "")[:10]
        if period_start.isoformat() <= created_date <= period_end.isoformat():
            matches_created += 1
            if booking_data.get("status") == "completed":
                matches_completed += 1
            if booking_data.get("disputed"):
                matches_with_disputes += 1

    completion_rate = (
        (matches_completed / matches_created * 100) if matches_created > 0 else 0
    )

    no_show_rate = (
        ((matches_created - matches_completed) / matches_created * 100)
        if matches_created > 0 else 0
    )

    dispute_rate = (
        (matches_with_disputes / matches_completed * 100)
        if matches_completed > 0 else 0
    )

    return MatchCompletionMetric(
        period_start=period_start,
        period_end=period_end,
        matches_created=matches_created,
        matches_completed=matches_completed,
        completion_rate=round(completion_rate, 2),
        no_show_rate=round(no_show_rate, 2),
        avg_actual_attendance=0.0,  # TODO: track attendance per match
        matches_with_disputes=matches_with_disputes,
        dispute_rate=round(dispute_rate, 2),
        reward_issued_after_completion=matches_completed,  # Approximate
    )


def get_captain_reward_metric(db: Client, captain_uid: str) -> CaptainRewardMetric:
    """Calculate captain-specific reward metrics."""
    from datetime import date
    from app.models.kpi import CaptainRewardMetric
    from app.services import rewards_service

    period_start = date.today().replace(day=1)
    period_end = date.today()

    stats = rewards_service.get_captain_stats(db, captain_uid)
    if not stats:
        raise HTTPException(status_code=404, detail="Captain not found")

    return CaptainRewardMetric(
        captain_uid=captain_uid,
        captain_name=stats.get("player_name", ""),
        period_start=period_start,
        period_end=period_end,
        total_credits_earned=stats.get("total_credits_earned", 0),
        matches_hosted=stats.get("matches_hosted", 0),
        matches_with_full_slots=0,  # TODO: calculate
        new_players_invited=stats.get("new_players_invited", 0),
        opponent_teams_invited=stats.get("opponent_teams_invited", 0),
        opponent_teams_accepted=stats.get("opponent_teams_accepted", 0),
        acceptance_rate=stats.get("acceptance_rate", 0),
        off_peak_matches=stats.get("off_peak_matches", 0),
        recurring_matches=stats.get("recurring_matches", 0),
        milestone_bonuses_earned=stats.get("milestone_bonuses_earned", 0),
        avg_credits_per_match=stats.get("avg_credits_per_match", 0),
    )
