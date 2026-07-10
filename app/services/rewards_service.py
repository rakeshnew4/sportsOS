"""Captain rewards program, referral tracking, and leaderboards."""

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.core.db import Client, FieldFilter


def rewards_collection(db: Client, uid: str):
    """Get rewards collection for a player."""
    return db.collection("players").document(uid).collection("rewards")


def referrals_collection(db: Client, uid: str):
    """Get referrals collection for a player."""
    return db.collection("players").document(uid).collection("referrals")


def list_player_rewards(db: Client, uid: str) -> list[dict]:
    """List all rewards earned by a player."""
    rewards = []
    for doc in rewards_collection(db, uid).order_by("issued_at", direction="DESCENDING").stream():
        data = doc.to_dict()
        rewards.append({
            "reward_id": doc.id,
            "player_uid": uid,
            **data,
        })
    return rewards


def get_captain_stats(db: Client, captain_uid: str) -> dict | None:
    """Get detailed statistics for a captain."""
    from app.models.kpi import PlayerKPIScope
    from app.services import kpi_service

    engagement = kpi_service.get_player_engagement_kpi(db, captain_uid, PlayerKPIScope.MONTH)
    if not engagement.is_captain:
        return None

    # Get additional captain-specific stats
    rewards = list_player_rewards(db, captain_uid)
    credits_earned_total = sum(r.get("credits_amount", 0) for r in rewards)

    # Count new players invited (referrals)
    referrals = []
    for doc in referrals_collection(db, captain_uid).stream():
        referrals.append(doc.to_dict())
    new_players_invited = len(referrals)

    # Count opponent teams invited
    opponent_teams_invited = len(
        list(db.collection("team_challenges").where(
            filter=FieldFilter("from_captain_uid", "==", captain_uid)
        ).stream())
    )

    # Count opponent teams accepted
    opponent_teams_accepted = len(
        list(db.collection("team_challenges").where(
            filter=FieldFilter("from_captain_uid", "==", captain_uid)
        ).where(filter=FieldFilter("status", "==", "accepted")).stream())
    )

    acceptance_rate = (
        (opponent_teams_accepted / opponent_teams_invited * 100)
        if opponent_teams_invited > 0 else 0
    )

    return {
        "player_uid": captain_uid,
        "player_name": engagement.display_name,
        "matches_hosted": engagement.teams_captained,
        "matches_completed": sum(1 for r in rewards if r.get("reward_type") == "match_completed"),
        "total_credits_earned": credits_earned_total,
        "credits_this_month": engagement.credits_earned,
        "new_players_invited": new_players_invited,
        "opponent_teams_invited": opponent_teams_invited,
        "opponent_teams_accepted": opponent_teams_accepted,
        "acceptance_rate": acceptance_rate,
        "off_peak_matches": sum(1 for r in rewards if r.get("reward_type") == "off_peak_bonus"),
        "recurring_matches": sum(1 for r in rewards if r.get("reward_type") == "recurring_setup"),
        "avg_credits_per_match": (
            (credits_earned_total / engagement.teams_captained)
            if engagement.teams_captained > 0 else 0
        ),
        "milestone_bonuses_earned": sum(1 for r in rewards if r.get("reward_type") == "milestone"),
        "last_match_date": engagement.period_end.isoformat() if engagement.period_end else None,
    }


def issue_reward(
    db: Client, player_uid: str, reward_type: str, credits_amount: float,
    reason: str, related_booking_id: str | None = None
) -> dict:
    """Issue a reward to a player (internal use after match completion)."""
    reward_id = str(uuid.uuid4())
    reward_data = {
        "reward_id": reward_id,
        "player_uid": player_uid,
        "reward_type": reward_type,
        "credits_amount": credits_amount,
        "reason": reason,
        "related_booking_id": related_booking_id,
        "issued_at": datetime.now(timezone.utc).isoformat(),
        "status": "issued",
    }
    rewards_collection(db, player_uid).document(reward_id).set(reward_data)

    # Also credit the wallet
    from app.services import wallet_service
    wallet_service.credit_wallet(db, player_uid, credits_amount, reason, related_booking_id)

    return reward_data


def get_leaderboard_credits_monthly(db: Client, limit: int = 10) -> list[dict]:
    """Leaderboard of captains by credits earned this month."""
    from datetime import date
    from dateutil.relativedelta import relativedelta

    start_date = (date.today().replace(day=1)).isoformat()
    end_date = date.today().isoformat()

    captains = {}
    for doc in db.collection("players").stream():
        captain_uid = doc.id
        stats = get_captain_stats(db, captain_uid)
        if stats:
            captains[captain_uid] = stats

    # Sort by credits earned this month
    sorted_captains = sorted(
        captains.values(),
        key=lambda x: x["credits_this_month"],
        reverse=True
    )[:limit]

    return sorted_captains


def get_leaderboard_matches_hosted_monthly(db: Client, limit: int = 10) -> list[dict]:
    """Leaderboard of captains by matches hosted this month."""
    captains = {}
    for doc in db.collection("players").stream():
        captain_uid = doc.id
        stats = get_captain_stats(db, captain_uid)
        if stats:
            captains[captain_uid] = stats

    # Sort by matches hosted this month
    sorted_captains = sorted(
        captains.values(),
        key=lambda x: x["matches_hosted"],
        reverse=True
    )[:limit]

    return sorted_captains


def get_leaderboard_referrals(db: Client, limit: int = 10) -> list[dict]:
    """Leaderboard of captains by new players they've brought to platform."""
    captains = {}
    for doc in db.collection("players").stream():
        captain_uid = doc.id
        stats = get_captain_stats(db, captain_uid)
        if stats:
            captains[captain_uid] = stats

    # Sort by new players invited
    sorted_captains = sorted(
        captains.values(),
        key=lambda x: x["new_players_invited"],
        reverse=True
    )[:limit]

    return sorted_captains


def list_player_referrals(db: Client, referrer_uid: str) -> list[dict]:
    """Get all players referred by a captain."""
    referrals = []
    for doc in referrals_collection(db, referrer_uid).stream():
        data = doc.to_dict()
        referrals.append({
            "referral_id": doc.id,
            "referrer_uid": referrer_uid,
            **data,
        })
    return referrals


def get_referral_earnings_summary(db: Client, player_uid: str) -> dict:
    """Get referral earnings summary for a player."""
    referrals = list_player_referrals(db, player_uid)
    total_referrals = len(referrals)
    total_credits_earned = sum(r.get("credits_earned", 0) for r in referrals)
    avg_ltv = (
        (total_credits_earned / total_referrals)
        if total_referrals > 0 else 0
    )

    # Count referrals this month
    from datetime import datetime, date
    today = date.today()
    referrals_this_month = sum(
        1 for r in referrals
        if r.get("referred_at", "").startswith(today.strftime("%Y-%m"))
    )

    # TODO: Get top referrer rank (requires global leaderboard)
    top_referrer_rank = None

    return {
        "total_referrals": total_referrals,
        "total_credits_earned": total_credits_earned,
        "avg_ltv": avg_ltv,
        "referrals_this_month": referrals_this_month,
        "top_referrer_rank": top_referrer_rank,
    }


def create_referral_code(db: Client, player_uid: str) -> str:
    """Create a unique referral code for a player."""
    code = f"SPORTSOS_{player_uid[:8].upper()}_{uuid.uuid4().hex[:6].upper()}"

    db.collection("referral_codes").document(code).set({
        "player_uid": player_uid,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "active": True,
    })

    return code


def register_referral(
    db: Client, referrer_uid: str, referred_player_uid: str,
    referred_player_name: str
) -> dict:
    """Register a new player as referred by an existing captain."""
    referral_id = str(uuid.uuid4())
    referral_data = {
        "referral_id": referral_id,
        "referred_player_uid": referred_player_uid,
        "referred_player_name": referred_player_name,
        "referred_at": datetime.now(timezone.utc).isoformat(),
        "first_match_date": None,
        "credits_earned": 0,
        "referrer_ltv": None,
    }

    referrals_collection(db, referrer_uid).document(referral_id).set(referral_data)

    # Issue referral bonus to referrer (after first match completion)
    # TODO: Implement in booking_service.complete_match() to check for referrer and issue bonus

    return referral_data
