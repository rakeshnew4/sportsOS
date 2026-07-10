"""Captain rewards program and referral tracking."""

from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import date

from app.core.db import Client, get_db
from app.core.security import CurrentUser, get_current_user

router = APIRouter(prefix="/rewards", tags=["rewards"])


class RewardRecord(BaseModel):
    reward_id: str
    player_uid: str
    reward_type: str
    credits_amount: float
    reason: str
    related_booking_id: str | None = None
    issued_at: str
    status: str


class CaptainStatsResponse(BaseModel):
    player_uid: str
    player_name: str
    matches_hosted: int
    matches_completed: int
    total_credits_earned: float
    credits_this_month: float
    new_players_invited: int
    opponent_teams_invited: int
    opponent_teams_accepted: int
    acceptance_rate: float
    off_peak_matches: int
    recurring_matches: int
    avg_credits_per_match: float
    milestone_bonuses_earned: int
    last_match_date: str | None = None


class CaptainLeaderboardEntry(BaseModel):
    rank: int
    player_uid: str
    player_name: str
    credits_earned_month: float
    matches_hosted_month: int
    new_players_brought: int
    acceptance_rate: float


class ReferralTracking(BaseModel):
    referral_id: str
    referrer_uid: str
    referred_player_uid: str
    referred_player_name: str
    referred_at: str
    first_match_date: str | None = None
    credits_earned: float
    referrer_ltv: float | None = None


# Captain Rewards

@router.get("/me/history")
def get_my_rewards(
    user: CurrentUser = Depends(get_current_user),
    db: Client = Depends(get_db),
) -> list[RewardRecord]:
    """Get all rewards earned by current player."""
    from app.services import rewards_service
    rewards = rewards_service.list_player_rewards(db, user.uid)
    return [RewardRecord(**r) for r in rewards]


@router.get("/me/captain")
def get_my_captain_stats(
    user: CurrentUser = Depends(get_current_user),
    db: Client = Depends(get_db),
) -> CaptainStatsResponse:
    """Get detailed captain statistics for current player."""
    from app.services import rewards_service
    stats = rewards_service.get_captain_stats(db, user.uid)
    if not stats:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No captain data")
    return CaptainStatsResponse(**stats)


@router.get("/{player_uid}/captain")
def get_captain_stats(
    player_uid: str,
    db: Client = Depends(get_db),
) -> CaptainStatsResponse:
    """Get captain statistics for a specific player (public)."""
    from app.services import rewards_service
    stats = rewards_service.get_captain_stats(db, player_uid)
    if not stats:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No captain data")
    return CaptainStatsResponse(**stats)


# Leaderboards

@router.get("/leaderboard/credits-monthly")
def leaderboard_credits_monthly(
    limit: int = 10,
    db: Client = Depends(get_db),
) -> list[CaptainLeaderboardEntry]:
    """Leaderboard of captains by credits earned this month."""
    from app.services import rewards_service
    entries = rewards_service.get_leaderboard_credits_monthly(db, limit)
    return [CaptainLeaderboardEntry(
        rank=i+1,
        player_uid=e["player_uid"],
        player_name=e["player_name"],
        credits_earned_month=e["credits_this_month"],
        matches_hosted_month=e["matches_hosted"],
        new_players_brought=e["new_players_invited"],
        acceptance_rate=e["acceptance_rate"],
    ) for i, e in enumerate(entries)]


@router.get("/leaderboard/matches-hosted")
def leaderboard_matches_hosted(
    limit: int = 10,
    db: Client = Depends(get_db),
) -> list[CaptainLeaderboardEntry]:
    """Leaderboard of captains by matches hosted this month."""
    from app.services import rewards_service
    entries = rewards_service.get_leaderboard_matches_hosted_monthly(db, limit)
    return [CaptainLeaderboardEntry(
        rank=i+1,
        player_uid=e["player_uid"],
        player_name=e["player_name"],
        credits_earned_month=e["credits_this_month"],
        matches_hosted_month=e["matches_hosted"],
        new_players_brought=e["new_players_invited"],
        acceptance_rate=e["acceptance_rate"],
    ) for i, e in enumerate(entries)]


@router.get("/leaderboard/new-players-referred")
def leaderboard_referrals(
    limit: int = 10,
    db: Client = Depends(get_db),
) -> list[CaptainLeaderboardEntry]:
    """Leaderboard of captains by new players they've brought to platform."""
    from app.services import rewards_service
    entries = rewards_service.get_leaderboard_referrals(db, limit)
    return [CaptainLeaderboardEntry(
        rank=i+1,
        player_uid=e["player_uid"],
        player_name=e["player_name"],
        credits_earned_month=e["credits_this_month"],
        matches_hosted_month=e["matches_hosted"],
        new_players_brought=e["new_players_invited"],
        acceptance_rate=e["acceptance_rate"],
    ) for i, e in enumerate(entries)]


# Referrals

@router.get("/me/referrals")
def get_my_referrals(
    user: CurrentUser = Depends(get_current_user),
    db: Client = Depends(get_db),
) -> list[ReferralTracking]:
    """Get all players referred by current captain."""
    from app.services import rewards_service
    referrals = rewards_service.list_player_referrals(db, user.uid)
    return [ReferralTracking(**r) for r in referrals]


@router.get("/me/referral-earnings")
def get_my_referral_earnings(
    user: CurrentUser = Depends(get_current_user),
    db: Client = Depends(get_db),
) -> dict:
    """Get referral earnings summary."""
    from app.services import rewards_service
    summary = rewards_service.get_referral_earnings_summary(db, user.uid)
    return {
        "total_referrals": summary.get("total_referrals", 0),
        "total_credits_earned": summary.get("total_credits_earned", 0),
        "avg_ltv_per_referral": summary.get("avg_ltv", 0),
        "referrals_this_month": summary.get("referrals_this_month", 0),
        "top_referrer_rank": summary.get("top_referrer_rank"),
    }


@router.post("/me/referrals/create-code")
def create_referral_code(
    user: CurrentUser = Depends(get_current_user),
    db: Client = Depends(get_db),
) -> dict:
    """Create a referral code for sharing with others."""
    from app.services import rewards_service
    code = rewards_service.create_referral_code(db, user.uid)
    return {
        "referral_code": code,
        "share_link": f"https://sportsos.app/join?ref={code}",
        "description": "Share this code with friends. You'll earn ₹40-50 credits when they join!",
    }
