"""KPI and analytics models — measure business outcomes, not just features."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class VenueKPIScope(str, Enum):
    TODAY = "today"
    WEEK = "week"
    MONTH = "month"
    CUSTOM = "custom"


class RevenueMetric(BaseModel):
    total_revenue: float = Field(..., description="Total revenue in INR")
    transaction_count: int = Field(..., description="Number of transactions")
    avg_transaction_value: float = Field(..., description="Average revenue per transaction")
    recurring_revenue: float = Field(..., description="Subscription/membership revenue")
    transaction_revenue: float = Field(..., description="One-time transaction revenue")


class OccupancyMetric(BaseModel):
    court_id: str
    court_name: str
    sport: str
    utilization_percent: float = Field(..., description="Booked hours / available hours * 100")
    booked_hours: float = Field(..., description="Total hours booked in period")
    available_hours: float = Field(..., description="Total operating hours in period")
    bookings_count: int = Field(..., description="Number of bookings in period")
    no_show_count: int = Field(..., description="Number of bookings that went to waste")
    cancelled_count: int = Field(..., description="Number of bookings cancelled by player")


class CustomerMetric(BaseModel):
    active_customers: int = Field(..., description="Unique players who booked in period")
    new_customers: int = Field(..., description="Players who booked for first time in period")
    returning_customers: int = Field(..., description="Players who booked 2+ times in period")
    repeat_booking_percent: float = Field(..., description="(Returning / Active) * 100")
    avg_lifetime_value: float = Field(..., description="Average spend per player across all time")


class TeamMetric(BaseModel):
    """Team formation and participation metrics."""
    teams_formed: int = Field(..., description="Total teams created in period")
    avg_team_size: float = Field(..., description="Average players per team")
    total_team_participants: int = Field(..., description="Total players across all teams")
    teams_completed: int = Field(..., description="Teams that completed their booking")


class MatchmakingMetric(BaseModel):
    """Join Match queue performance."""
    total_queued: int = Field(..., description="Total players who queued in period")
    matches_formed: int = Field(..., description="Completed matches from queue")
    match_fill_rate: float = Field(..., description="(Players matched / Total queued) * 100")
    avg_fill_time_seconds: float = Field(..., description="Average time to fill a match from first queue to formation")
    queue_cancellations: int = Field(..., description="Players who dropped out of queue")
    cancellation_rate: float = Field(..., description="(Cancellations / Queued) * 100")


class VenueOverviewKPI(BaseModel):
    """Venue north star metrics for today."""
    venue_name: str
    scope: VenueKPIScope
    period_start: date
    period_end: date
    revenue: RevenueMetric
    occupancy: list[OccupancyMetric] = Field(..., description="Per-court utilization")
    customers: CustomerMetric
    teams: TeamMetric
    matchmaking: MatchmakingMetric
    captain_rewards: CaptainRewardMetric | None = Field(None, description="Rewards issued at this venue")
    match_completion: MatchCompletionMetric
    avg_occupancy_percent: float = Field(..., description="Weighted average across all courts")


class PlayerKPIScope(str, Enum):
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"
    ALL_TIME = "all_time"


class CaptainRewardMetric(BaseModel):
    """Captain rewards program effectiveness."""
    captain_uid: str
    captain_name: str
    period_start: date
    period_end: date
    total_credits_earned: float = Field(..., description="Total credits earned from hosting")
    matches_hosted: int = Field(..., description="Matches organized as captain")
    matches_with_full_slots: int = Field(..., description="Matches where all slots filled")
    new_players_invited: int = Field(..., description="Unique new players brought to platform")
    opponent_teams_invited: int = Field(..., description="Teams invited for team-vs-team matches")
    opponent_teams_accepted: int = Field(..., description="Invitations that were accepted")
    acceptance_rate: float = Field(..., description="(Accepted / Invited) * 100 for opponent teams")
    off_peak_matches: int = Field(..., description="Matches booked during off-peak hours")
    recurring_matches: int = Field(..., description="Recurring weekly/recurring matches created")
    milestone_bonuses_earned: int = Field(..., description="Number of milestone bonuses (e.g., 10 matches)")
    avg_credits_per_match: float = Field(..., description="Average credits earned per match hosted")


class CreditsMetric(BaseModel):
    """SportsOS Credits system performance."""
    period_start: date
    period_end: date
    total_credits_issued: float = Field(..., description="Total credits created (from rewards)")
    total_credits_redeemed: float = Field(..., description="Total credits used for bookings/services")
    total_credits_outstanding: float = Field(..., description="Credits in circulation (issued - redeemed)")
    redemption_rate: float = Field(..., description="(Redeemed / Issued) * 100")
    avg_credits_per_captain: float = Field(..., description="Average credits earned per active captain")
    avg_redemption_value: float = Field(..., description="Average booking value when credits are redeemed")
    cost_of_rewards: float = Field(..., description="Cost to platform of issued credits (GMV %)")
    reward_roi: float = Field(..., description="(Revenue from new players / Cost of rewards) * 100")


class TeamNetworkMetric(BaseModel):
    """Team-to-team network growth and engagement."""
    period_start: date
    period_end: date
    teams_active: int = Field(..., description="Unique teams with recent activity")
    new_teams: int = Field(..., description="New teams formed in period")
    team_vs_team_matches: int = Field(..., description="Matches organized between two teams")
    avg_team_size: float = Field(..., description="Average players per team")
    avg_team_rating: float = Field(..., description="Average skill rating across all teams")
    teams_with_10_plus_matches: int = Field(..., description="Mature teams with 10+ completed matches")
    friendly_challenge_count: int = Field(..., description="'Looking for opponent' requests created")
    challenge_acceptance_rate: float = Field(..., description="(Accepted / Created) * 100")
    repeat_matchups: int = Field(..., description="Same two teams playing multiple times")


class ReferralMetric(BaseModel):
    """New player acquisition through existing players."""
    period_start: date
    period_end: date
    new_players_total: int = Field(..., description="Total new players in period")
    new_players_from_referrals: int = Field(..., description="New players brought by existing captains")
    referral_rate: float = Field(..., description="(From referrals / Total new) * 100")
    avg_lifetime_value_referred: float = Field(..., description="LTV of players brought by referrals")
    top_referrer_uid: str | None = Field(None, description="Captain who brought most new players")
    top_referrer_count: int = Field(None, description="Count for top referrer")
    referral_credit_cost: float = Field(..., description="Total credits issued for referrals in period")


class MatchCompletionMetric(BaseModel):
    """Match quality and completion tracking (prerequisite for reward issuance)."""
    period_start: date
    period_end: date
    matches_created: int = Field(..., description="Total bookings/matches created")
    matches_completed: int = Field(..., description="Matches with QR check-in completed")
    completion_rate: float = Field(..., description="(Completed / Created) * 100")
    no_show_rate: float = Field(..., description="(No-shows / Created) * 100")
    avg_actual_attendance: float = Field(..., description="Average % of booked slots that checked in")
    matches_with_disputes: int = Field(..., description="Matches flagged for payment disputes")
    dispute_rate: float = Field(..., description="(With disputes / Completed) * 100")
    reward_issued_after_completion: int = Field(..., description="Matches that triggered captain rewards")


class PlayerEngagementKPI(BaseModel):
    """Player-level stats."""
    uid: str
    display_name: str
    scope: PlayerKPIScope
    period_start: date
    period_end: date
    matches_played: int = Field(..., description="Total matches joined")
    teams_captained: int = Field(..., description="Teams created (captain role)")
    teams_joined: int = Field(..., description="Teams joined as member")
    courts_booked: int = Field(..., description="Total court bookings (captain role)")
    hours_played: float = Field(..., description="Total hours in completed bookings/matches")
    bookings_this_period: int = Field(..., description="Active bookings in period")
    wallet_total_spend: float = Field(..., description="Total debited from wallet in period")
    wallet_balance: float = Field(..., description="Current wallet balance")
    credits_earned: float = Field(..., description="SportsOS Credits earned from hosting (this period)")
    credits_redeemed: float = Field(..., description="SportsOS Credits used for bookings (this period)")
    credits_outstanding: float = Field(..., description="Unredeemed credits available")
    weekly_sessions: float = Field(..., description="Average sessions per week")
    favorite_venue: str | None = Field(None, description="Most-booked venue")
    favorite_sport: str | None = Field(None, description="Most-played sport")
    repeat_venues: int = Field(..., description="Number of unique venues visited")
    players_referred: int = Field(..., description="New players brought to platform by this player")
    is_captain: bool = Field(..., description="Has hosted at least one match")
    is_active_captain: bool = Field(..., description="Hosted 2+ matches in period")


class PlatformAdminKPI(BaseModel):
    """System-level health metrics for dashboard."""
    snapshot_date: datetime
    # Venues & Venues
    active_venues: int = Field(..., description="Venues with activity in last 30 days")
    total_venues: int
    active_players: int = Field(..., description="Players with activity in last 30 days")
    total_players: int
    active_captains: int = Field(..., description="Players who hosted 1+ matches in last 30 days")
    daily_active_users: int = Field(..., description="Users with activity today")
    monthly_active_users: int = Field(..., description="Users with activity this month")
    # Bookings & Matches
    bookings_today: int
    bookings_this_month: int
    matches_formed_today: int = Field(..., description="Join Match queue formations")
    matches_formed_this_month: int
    team_vs_team_matches_month: int = Field(..., description="Team-to-team matches organized")
    # Revenue & Economics
    gmv_today: float = Field(..., description="Gross Merchandise Value (all transactions)")
    gmv_this_month: float
    mrr: float = Field(..., description="Monthly Recurring Revenue (subscriptions/memberships)")
    arr: float = Field(..., description="Annual Recurring Revenue")
    credits_issued_this_month: float = Field(..., description="Total SportsOS Credits issued as rewards")
    credits_redeemed_this_month: float = Field(..., description="Total SportsOS Credits redeemed")
    reward_cost_percent: float = Field(..., description="(Credits issued / GMV) * 100")
    # Teams & Network
    total_teams: int = Field(..., description="Total teams on platform")
    active_teams: int = Field(..., description="Teams with activity in last 30 days")
    team_vs_team_acceptance_rate: float = Field(..., description="% of team challenges accepted")
    # Referrals & Growth
    new_players_this_month: int
    new_players_from_referrals: int = Field(..., description="New players referred by existing captains")
    organic_referral_rate: float = Field(..., description="(From referrals / Total new) * 100")
    # Quality & Health
    payment_success_rate: float = Field(..., description="% of attempted transactions that succeeded")
    match_completion_rate: float = Field(..., description="% of booked matches that completed (QR check-in)")
    match_dispute_rate: float = Field(..., description="% of matches flagged for payment disputes")
    player_retention_7d: float = Field(..., description="% of players active 7+ days ago who are still active")
    player_retention_30d: float = Field(..., description="% of players active 30+ days ago who are still active")
    churn_rate: float = Field(..., description="% of players who were active last month but not this month")
    captain_retention_30d: float = Field(..., description="% of captains from last month who hosted again")
