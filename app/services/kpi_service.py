"""KPI and analytics calculation service — PostgreSQL-backed."""

from datetime import date, datetime, timedelta
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.orm import (
    Booking, BookingParticipant, Court, MatchRequest, Referral,
    Reward, Team, TeamChallenge, TeamMember, Tenant, User, Wallet, WalletTransaction,
)
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


def _period(scope: VenueKPIScope) -> tuple[date, date]:
    today = date.today()
    if scope == VenueKPIScope.TODAY:
        return today, today
    if scope == VenueKPIScope.WEEK:
        return today - timedelta(days=today.weekday()), today
    if scope == VenueKPIScope.MONTH:
        return date(today.year, today.month, 1), today
    raise ValueError(f"Unknown scope: {scope}")


def get_venue_overview_kpi(
    db: Session, tenant_id: str, scope: VenueKPIScope = VenueKPIScope.TODAY
) -> VenueOverviewKPI:
    period_start, period_end = _period(scope)

    # Revenue
    confirmed_bookings = (
        db.query(Booking)
        .filter(
            Booking.tenant_id == tenant_id,
            Booking.status == "confirmed",
            Booking.date >= period_start.isoformat(),
            Booking.date <= period_end.isoformat(),
        )
        .all()
    )
    revenue_amount = sum(b.price for b in confirmed_bookings)
    transaction_count = len(confirmed_bookings)
    avg_transaction = revenue_amount / transaction_count if transaction_count else 0.0

    # Occupancy per court
    courts = db.query(Court).filter(Court.tenant_id == tenant_id).all()
    occupancy_list: list[OccupancyMetric] = []
    for court in courts:
        court_bookings = (
            db.query(Booking)
            .filter(
                Booking.tenant_id == tenant_id,
                Booking.court_id == court.court_id,
                Booking.date >= period_start.isoformat(),
                Booking.date <= period_end.isoformat(),
            )
            .all()
        )
        booked_hours = 0.0
        bookings_count = 0
        cancellations = 0
        for b in court_bookings:
            if b.status == "confirmed":
                bookings_count += 1
                try:
                    booked_hours += int(b.end_time.split(":")[0]) - int(b.start_time.split(":")[0])
                except (ValueError, IndexError):
                    pass
            elif b.status == "cancelled":
                cancellations += 1
        try:
            daily_hours = int(court.close_time.split(":")[0]) - int(court.open_time.split(":")[0])
        except (ValueError, IndexError):
            daily_hours = 12
        days_in_period = (period_end - period_start).days + 1
        available_hours = daily_hours * days_in_period
        utilization_pct = (booked_hours / available_hours * 100) if available_hours > 0 else 0.0
        occupancy_list.append(OccupancyMetric(
            court_id=court.court_id, court_name=court.name, sport=court.sport,
            utilization_percent=round(utilization_pct, 2), booked_hours=booked_hours,
            available_hours=available_hours, bookings_count=bookings_count,
            no_show_count=0, cancelled_count=cancellations,
        ))

    avg_occupancy = sum(o.utilization_percent for o in occupancy_list) / len(occupancy_list) if occupancy_list else 0.0

    # Customers
    player_booking_counts: dict[str, int] = {}
    for b in confirmed_bookings:
        player_booking_counts[b.created_by] = player_booking_counts.get(b.created_by, 0) + 1
    participants = (
        db.query(BookingParticipant)
        .join(Booking, Booking.booking_id == BookingParticipant.booking_id)
        .filter(Booking.tenant_id == tenant_id)
        .all()
    )
    for p in participants:
        player_booking_counts[p.uid] = player_booking_counts.get(p.uid, 0) + 1
    active_players = len(player_booking_counts)
    returning = sum(1 for c in player_booking_counts.values() if c >= 2)
    repeat_pct = (returning / active_players * 100) if active_players else 0.0
    ltv = revenue_amount / active_players if active_players else 0.0
    customers = CustomerMetric(
        active_customers=active_players, new_customers=0,
        returning_customers=returning, repeat_booking_percent=round(repeat_pct, 2),
        avg_lifetime_value=round(ltv, 2),
    )

    # Matchmaking
    mrs = (
        db.query(MatchRequest)
        .filter(
            MatchRequest.tenant_id == tenant_id,
            MatchRequest.date >= period_start.isoformat(),
            MatchRequest.date <= period_end.isoformat(),
        )
        .all()
    )
    queued = {mr.uid for mr in mrs}
    matched = {mr.uid for mr in mrs if mr.status == "matched"}
    q_cancellations = sum(1 for mr in mrs if mr.status == "cancelled")
    fill_rate = (len(matched) / len(queued) * 100) if queued else 0.0
    matchmaking = MatchmakingMetric(
        total_queued=len(queued), matches_formed=sum(1 for mr in mrs if mr.status == "matched"),
        match_fill_rate=round(fill_rate, 2), avg_fill_time_seconds=0.0,
        queue_cancellations=q_cancellations, cancellation_rate=0.0,
    )

    # Teams
    team_ids = {b.team_id for b in db.query(Booking).filter(
        Booking.tenant_id == tenant_id,
        Booking.date >= period_start.isoformat(),
        Booking.date <= period_end.isoformat(),
        Booking.team_id.isnot(None),
    ).all()}
    completed_team_ids = {b.team_id for b in db.query(Booking).filter(
        Booking.tenant_id == tenant_id, Booking.status == "completed", Booking.team_id.isnot(None)
    ).all()}
    total_members = db.query(TeamMember).filter(TeamMember.team_id.in_(team_ids)).count() if team_ids else 0
    avg_team_size = total_members / len(team_ids) if team_ids else 0.0
    teams_metric = TeamMetric(
        teams_formed=len(team_ids), avg_team_size=round(avg_team_size, 2),
        total_team_participants=total_members, teams_completed=len(completed_team_ids),
    )

    # Match completion
    all_bookings_period = (
        db.query(Booking)
        .filter(Booking.tenant_id == tenant_id, Booking.date >= period_start.isoformat(), Booking.date <= period_end.isoformat())
        .all()
    )
    completed_count = sum(1 for b in all_bookings_period if b.status == "completed")
    completion_rate = (completed_count / len(all_bookings_period) * 100) if all_bookings_period else 0.0
    match_completion = MatchCompletionMetric(
        period_start=period_start, period_end=period_end,
        matches_created=len(all_bookings_period), matches_completed=completed_count,
        completion_rate=round(completion_rate, 2), no_show_rate=0.0, avg_actual_attendance=0.0,
        matches_with_disputes=0, dispute_rate=0.0, reward_issued_after_completion=0,
    )

    # Venue name
    tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    venue_name = tenant.name if tenant else "?"

    return VenueOverviewKPI(
        venue_name=venue_name, scope=scope, period_start=period_start, period_end=period_end,
        revenue=RevenueMetric(
            total_revenue=round(revenue_amount, 2), transaction_count=transaction_count,
            avg_transaction_value=round(avg_transaction, 2), recurring_revenue=0.0,
            transaction_revenue=revenue_amount,
        ),
        occupancy=occupancy_list, customers=customers, teams=teams_metric,
        matchmaking=matchmaking, match_completion=match_completion,
        avg_occupancy_percent=round(avg_occupancy, 2),
    )


def get_player_engagement_kpi(
    db: Session, uid: str, scope: PlayerKPIScope = PlayerKPIScope.MONTH
) -> PlayerEngagementKPI:
    today = date.today()
    if scope == PlayerKPIScope.MONTH:
        period_start = today.replace(day=1)
        period_end = today
    elif scope == PlayerKPIScope.QUARTER:
        qm = ((today.month - 1) // 3) * 3 + 1
        period_start = date(today.year, qm, 1)
        period_end = today
    elif scope == PlayerKPIScope.YEAR:
        period_start = date(today.year, 1, 1)
        period_end = today
    else:
        period_start = date(1970, 1, 1)
        period_end = date(2100, 12, 31)

    user = db.query(User).filter(User.uid == uid).first()
    display_name = user.display_name if user else uid

    my_bookings = (
        db.query(Booking)
        .filter(Booking.created_by == uid, Booking.status == "confirmed",
                Booking.date >= period_start.isoformat(), Booking.date <= period_end.isoformat())
        .all()
    )
    my_participations = (
        db.query(BookingParticipant)
        .filter(BookingParticipant.uid == uid)
        .join(Booking, Booking.booking_id == BookingParticipant.booking_id)
        .filter(Booking.date >= period_start.isoformat(), Booking.date <= period_end.isoformat())
        .all()
    )

    total_hours = sum(
        (int(b.end_time.split(":")[0]) - int(b.start_time.split(":")[0])) for b in my_bookings
    )
    total_spend = sum(b.price for b in my_bookings)
    sports_played = {}
    for b in my_bookings:
        sports_played[b.sport] = sports_played.get(b.sport, 0) + 1
    favorite_sport = max(sports_played, key=sports_played.get) if sports_played else None
    venues_visited = {b.tenant_id for b in my_bookings}

    wallet = db.query(Wallet).filter(Wallet.uid == uid).first()
    wallet_balance = wallet.balance if wallet else 0.0

    teams_captained = db.query(Team).filter(
        Team.captain_uid == uid, Team.created_at >= datetime(period_start.year, period_start.month, period_start.day)
    ).count()
    teams_joined = db.query(TeamMember).join(Team, Team.team_id == TeamMember.team_id).filter(
        TeamMember.uid == uid, Team.captain_uid != uid
    ).count()

    from app.services import rewards_service
    rewards = rewards_service.list_player_rewards(db, uid)
    credits_earned = round(sum(
        r.get("credits_amount", 0.0) for r in rewards
        if period_start.isoformat() <= r.get("issued_at", "")[:10] <= period_end.isoformat()
    ), 2)
    referrals = rewards_service.list_player_referrals(db, uid)
    players_referred = len(referrals)

    booking_dates = {b.date for b in my_bookings}
    days_in_period = (period_end - period_start).days or 1
    weekly_sessions = len(booking_dates) / (days_in_period / 7.0) if booking_dates else 0.0

    return PlayerEngagementKPI(
        uid=uid, display_name=display_name, scope=scope,
        period_start=period_start, period_end=period_end,
        matches_played=len(my_participations),
        teams_captained=teams_captained, teams_joined=teams_joined,
        courts_booked=len(my_bookings), hours_played=round(total_hours, 1),
        bookings_this_period=len(my_bookings),
        wallet_total_spend=round(total_spend, 2), wallet_balance=round(wallet_balance, 2),
        credits_earned=credits_earned, credits_redeemed=round(total_spend, 2),
        credits_outstanding=round(wallet_balance, 2),
        weekly_sessions=round(weekly_sessions, 2), favorite_venue=None,
        favorite_sport=favorite_sport, repeat_venues=len(venues_visited),
        players_referred=players_referred,
        is_captain=teams_captained > 0, is_active_captain=teams_captained >= 2,
    )


def get_platform_admin_kpi(db: Session) -> PlatformAdminKPI:
    today = date.today()
    month_ago = today - timedelta(days=30)

    total_venues = db.query(Tenant).count()
    total_players = db.query(User).filter(User.is_player == True).count()

    bookings_today = db.query(Booking).filter(
        Booking.status == "confirmed", Booking.date == today.isoformat()
    ).count()
    bookings_month = db.query(Booking).filter(
        Booking.status == "confirmed", Booking.date >= month_ago.isoformat()
    ).count()

    gmv_today = sum(
        b.price for b in db.query(Booking).filter(Booking.status == "confirmed", Booking.date == today.isoformat()).all()
    )
    gmv_month = sum(
        b.price for b in db.query(Booking).filter(Booking.status == "confirmed", Booking.date >= month_ago.isoformat()).all()
    )

    dau = db.query(Booking.created_by).filter(Booking.date == today.isoformat()).distinct().count()
    mau = db.query(Booking.created_by).filter(Booking.date >= month_ago.isoformat()).distinct().count()

    matches_formed_month = db.query(MatchRequest).filter(
        MatchRequest.status == "matched", MatchRequest.date >= month_ago.isoformat()
    ).count()

    total_teams = db.query(Team).count()
    active_teams = db.query(Team).filter(Team.status == "active").count()

    challenges = db.query(TeamChallenge).count()
    accepted = db.query(TeamChallenge).filter(TeamChallenge.status == "accepted").count()
    acceptance_rate = (accepted / challenges * 100) if challenges else 0.0

    credits_metric = get_credits_metric(db)

    new_players_this_month = db.query(User).filter(
        User.created_at >= datetime(month_ago.year, month_ago.month, month_ago.day)
    ).count()
    new_players_from_referrals = db.query(Referral).filter(
        Referral.created_at >= datetime(month_ago.year, month_ago.month, month_ago.day)
    ).count()
    organic_referral_rate = (new_players_from_referrals / new_players_this_month * 100) if new_players_this_month else 0.0

    matches_created = db.query(Booking).filter(Booking.date >= month_ago.isoformat()).count()
    matches_completed = db.query(Booking).filter(Booking.status == "completed", Booking.date >= month_ago.isoformat()).count()
    match_completion_rate = (matches_completed / matches_created * 100) if matches_created else 0.0

    mrr = gmv_month / 12 if gmv_month else 0.0

    return PlatformAdminKPI(
        snapshot_date=datetime.now(),
        active_venues=db.query(Booking.tenant_id).filter(Booking.date >= month_ago.isoformat()).distinct().count(),
        total_venues=total_venues,
        active_players=mau, total_players=total_players,
        active_captains=db.query(Booking.created_by).filter(Booking.date >= month_ago.isoformat()).distinct().count(),
        daily_active_users=dau, monthly_active_users=mau,
        bookings_today=bookings_today, bookings_this_month=bookings_month,
        matches_formed_today=db.query(MatchRequest).filter(MatchRequest.status == "matched", MatchRequest.date == today.isoformat()).count(),
        matches_formed_this_month=matches_formed_month,
        team_vs_team_matches_month=accepted,
        gmv_today=round(gmv_today, 2), gmv_this_month=round(gmv_month, 2),
        mrr=round(mrr, 2), arr=round(mrr * 12, 2),
        credits_issued_this_month=round(credits_metric.total_credits_issued, 2),
        credits_redeemed_this_month=round(credits_metric.total_credits_redeemed, 2),
        reward_cost_percent=round((credits_metric.total_credits_issued / gmv_month * 100) if gmv_month else 0.0, 2),
        total_teams=total_teams, active_teams=active_teams,
        team_vs_team_acceptance_rate=round(acceptance_rate, 2),
        new_players_this_month=new_players_this_month,
        new_players_from_referrals=new_players_from_referrals,
        organic_referral_rate=round(organic_referral_rate, 2),
        payment_success_rate=95.0, match_completion_rate=round(match_completion_rate, 2),
        match_dispute_rate=0.0, player_retention_7d=0.0, player_retention_30d=0.0,
        captain_retention_30d=0.0, churn_rate=0.0,
    )


def get_credits_metric(db: Session) -> CreditsMetric:
    today = date.today()
    period_start = today.replace(day=1)
    period_end = today

    total_issued = sum(
        r.credits_amount for r in db.query(Reward).filter(
            Reward.issued_at >= datetime(period_start.year, period_start.month, 1)
        ).all()
    )
    total_outstanding = sum(w.balance for w in db.query(Wallet).all())
    total_redeemed = max(0.0, total_issued - total_outstanding)
    redemption_rate = (total_redeemed / total_issued * 100) if total_issued else 0.0

    return CreditsMetric(
        period_start=period_start, period_end=period_end,
        total_credits_issued=round(total_issued, 2),
        total_credits_redeemed=round(total_redeemed, 2),
        total_credits_outstanding=round(total_outstanding, 2),
        redemption_rate=round(redemption_rate, 2),
        avg_credits_per_captain=0.0, avg_redemption_value=0.0,
        cost_of_rewards=0.0, reward_roi=0.0,
    )


def get_team_network_metric(db: Session) -> TeamNetworkMetric:
    today = date.today()
    period_start = today.replace(day=1)
    period_end = today

    active_teams = db.query(Team).filter(Team.status == "active").count()
    new_teams = db.query(Team).filter(
        Team.created_at >= datetime(period_start.year, period_start.month, 1)
    ).count()
    tv_matches = db.query(TeamChallenge).filter(TeamChallenge.status == "accepted").count()
    challenges = db.query(TeamChallenge).count()
    acceptance_rate = (tv_matches / challenges * 100) if challenges else 0.0

    return TeamNetworkMetric(
        period_start=period_start, period_end=period_end,
        teams_active=active_teams, new_teams=new_teams,
        team_vs_team_matches=tv_matches, avg_team_size=0.0, avg_team_rating=0.0,
        teams_with_10_plus_matches=0, friendly_challenge_count=challenges,
        challenge_acceptance_rate=round(acceptance_rate, 2), repeat_matchups=0,
    )


def get_referral_metric(db: Session) -> ReferralMetric:
    today = date.today()
    period_start = today.replace(day=1)
    period_end = today

    new_players_total = db.query(User).filter(
        User.created_at >= datetime(period_start.year, period_start.month, 1)
    ).count()
    new_from_referrals = db.query(Referral).filter(
        Referral.created_at >= datetime(period_start.year, period_start.month, 1)
    ).count()
    referral_rate = (new_from_referrals / new_players_total * 100) if new_players_total else 0.0

    return ReferralMetric(
        period_start=period_start, period_end=period_end,
        new_players_total=new_players_total,
        new_players_from_referrals=new_from_referrals,
        referral_rate=round(referral_rate, 2),
        avg_lifetime_value_referred=0.0, top_referrer_uid=None, top_referrer_count=0,
        referral_credit_cost=0.0,
    )


def get_match_completion_metric(db: Session) -> MatchCompletionMetric:
    today = date.today()
    period_start = today.replace(day=1)
    period_end = today

    bookings = db.query(Booking).filter(
        Booking.date >= period_start.isoformat(), Booking.date <= period_end.isoformat()
    ).all()
    completed = sum(1 for b in bookings if b.status == "completed")
    completion_rate = (completed / len(bookings) * 100) if bookings else 0.0

    return MatchCompletionMetric(
        period_start=period_start, period_end=period_end,
        matches_created=len(bookings), matches_completed=completed,
        completion_rate=round(completion_rate, 2), no_show_rate=0.0,
        avg_actual_attendance=0.0, matches_with_disputes=0, dispute_rate=0.0,
        reward_issued_after_completion=completed,
    )


def get_captain_reward_metric(db: Session, captain_uid: str) -> CaptainRewardMetric:
    today = date.today()
    period_start = today.replace(day=1)
    period_end = today

    from app.services import rewards_service
    stats = rewards_service.get_captain_stats(db, captain_uid)
    if not stats:
        raise HTTPException(status_code=404, detail="Captain not found")

    return CaptainRewardMetric(
        captain_uid=captain_uid, captain_name=stats.get("player_name", ""),
        period_start=period_start, period_end=period_end,
        total_credits_earned=stats.get("total_credits_earned", 0),
        matches_hosted=stats.get("matches_hosted", 0),
        matches_with_full_slots=0, new_players_invited=stats.get("new_players_invited", 0),
        opponent_teams_invited=stats.get("opponent_teams_invited", 0),
        opponent_teams_accepted=stats.get("opponent_teams_accepted", 0),
        acceptance_rate=stats.get("acceptance_rate", 0),
        off_peak_matches=0, recurring_matches=0, milestone_bonuses_earned=0,
        avg_credits_per_match=0.0,
    )
