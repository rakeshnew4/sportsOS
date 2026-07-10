"""Captain rewards program, referral tracking, and leaderboards — PostgreSQL-backed."""

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.orm import Booking, Reward, Referral, TeamChallenge, User


def list_player_rewards(db: Session, uid: str) -> list[dict]:
    rewards = (
        db.query(Reward)
        .filter(Reward.uid == uid)
        .order_by(Reward.issued_at.desc())
        .all()
    )
    return [
        {
            "reward_id": r.reward_id,
            "player_uid": uid,
            "reward_type": r.reward_type,
            "credits_amount": r.credits_amount,
            "reason": r.reason,
            "related_booking_id": (r.data or {}).get("related_booking_id"),
            "issued_at": r.issued_at.isoformat(),
            "status": "issued",
        }
        for r in rewards
    ]


def issue_reward(
    db: Session, player_uid: str, reward_type: str, credits_amount: float,
    reason: str, related_booking_id: str | None = None,
) -> dict:
    reward_id = str(uuid.uuid4())
    reward = Reward(
        reward_id=reward_id,
        uid=player_uid,
        reward_type=reward_type,
        credits_amount=credits_amount,
        reason=reason,
        issued_at=datetime.now(timezone.utc),
        data={"related_booking_id": related_booking_id} if related_booking_id else {},
    )
    db.add(reward)
    from app.services import wallet_service
    wallet_service.credit_wallet(db, player_uid, credits_amount, reason, related_booking_id)
    # Caller is responsible for db.commit()
    return {
        "reward_id": reward_id,
        "player_uid": player_uid,
        "reward_type": reward_type,
        "credits_amount": credits_amount,
        "reason": reason,
        "issued_at": reward.issued_at.isoformat(),
    }


def get_captain_stats(db: Session, captain_uid: str) -> dict | None:
    user = db.query(User).filter(User.uid == captain_uid, User.is_player == True).first()
    if not user:
        return None
    rewards = list_player_rewards(db, captain_uid)
    credits_earned_total = sum(r.get("credits_amount", 0) for r in rewards)
    now = datetime.now(timezone.utc)
    credits_this_month = sum(
        r.get("credits_amount", 0) for r in rewards
        if datetime.fromisoformat(r["issued_at"]).year == now.year
        and datetime.fromisoformat(r["issued_at"]).month == now.month
    )
    referrals = db.query(Referral).filter(Referral.referrer_uid == captain_uid).count()
    challenges_sent = db.query(TeamChallenge).filter(TeamChallenge.from_captain_uid == captain_uid).count()
    challenges_accepted = (
        db.query(TeamChallenge)
        .filter(TeamChallenge.from_captain_uid == captain_uid, TeamChallenge.status == "accepted")
        .count()
    )
    hosted_bookings = db.query(Booking).filter(Booking.created_by == captain_uid).all()
    matches_hosted = len(hosted_bookings)
    completed_bookings = [b for b in hosted_bookings if b.status == "completed"]
    matches_completed = len(completed_bookings)
    last_match_date = max((b.date for b in completed_bookings), default=None)
    return {
        "player_uid": captain_uid,
        "player_name": user.display_name,
        "matches_hosted": matches_hosted,
        "matches_completed": matches_completed,
        "total_credits_earned": credits_earned_total,
        "credits_this_month": credits_this_month,
        "new_players_invited": referrals,
        "opponent_teams_invited": challenges_sent,
        "opponent_teams_accepted": challenges_accepted,
        "acceptance_rate": (challenges_accepted / challenges_sent * 100) if challenges_sent > 0 else 0,
        "off_peak_matches": 0,
        "recurring_matches": 0,
        "avg_credits_per_match": (credits_earned_total / matches_hosted) if matches_hosted > 0 else 0,
        "milestone_bonuses_earned": 0,
        "last_match_date": last_match_date,
    }


def get_leaderboard_credits_monthly(db: Session, limit: int = 10) -> list[dict]:
    users = db.query(User).filter(User.is_player == True).all()
    stats = [s for u in users if (s := get_captain_stats(db, u.uid)) is not None]
    return sorted(stats, key=lambda x: x["total_credits_earned"], reverse=True)[:limit]


def get_leaderboard_matches_hosted_monthly(db: Session, limit: int = 10) -> list[dict]:
    return get_leaderboard_credits_monthly(db, limit)


def get_leaderboard_referrals(db: Session, limit: int = 10) -> list[dict]:
    users = db.query(User).filter(User.is_player == True).all()
    stats = [s for u in users if (s := get_captain_stats(db, u.uid)) is not None]
    return sorted(stats, key=lambda x: x["new_players_invited"], reverse=True)[:limit]


def list_player_referrals(db: Session, referrer_uid: str) -> list[dict]:
    refs = db.query(Referral).filter(Referral.referrer_uid == referrer_uid).all()
    results = []
    for r in refs:
        referred_user = db.query(User).filter(User.uid == r.referred_uid).first()
        results.append({
            "referral_id": str(r.id),
            "referrer_uid": referrer_uid,
            "referred_player_uid": r.referred_uid,
            "referred_player_name": referred_user.display_name if referred_user else r.referred_uid,
            "referred_at": r.created_at.isoformat(),
            "first_match_date": None,
            "credits_earned": 0.0,
            "referrer_ltv": None,
        })
    return results


def get_referral_earnings_summary(db: Session, player_uid: str) -> dict:
    total = db.query(Referral).filter(Referral.referrer_uid == player_uid).count()
    return {"total_referrals": total, "total_credits_earned": 0.0, "referrals_this_month": 0}


def create_referral_code(db: Session, player_uid: str) -> str:
    return f"SPORTSOS_{player_uid[:8].upper()}_{uuid.uuid4().hex[:6].upper()}"


def register_referral(db: Session, referrer_uid: str, referred_player_uid: str, referred_player_name: str) -> dict:
    referral = Referral(referrer_uid=referrer_uid, referred_uid=referred_player_uid, created_at=datetime.now(timezone.utc))
    db.add(referral)
    return {"referrer_uid": referrer_uid, "referred_uid": referred_player_uid}
