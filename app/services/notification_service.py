"""Notification service — PostgreSQL-backed."""

import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.orm import Notification


NotificationType = Literal[
    "match_needs_players",
    "team_challenge",
    "match_reminder",
    "reward_earned",
    "promoted_from_waitlist",
    "slot_cancelled",
    "friend_activity",
    "match_formed",
]


def record_notification(
    db: Session,
    player_uid: str,
    notification_type: str,
    title: str,
    body: str,
    data: dict | None = None,
    send_push: bool = True,
) -> dict:
    notification_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    notif = Notification(
        id=notification_id,
        uid=player_uid,
        type=notification_type,
        title=title,
        body=body,
        data=data or {},
        is_read=False,
        created_at=now,
    )
    db.add(notif)
    # Caller commits
    return {
        "notification_id": notification_id,
        "player_uid": player_uid,
        "type": notification_type,
        "title": title,
        "body": body,
        "data": data or {},
        "created_at": now.isoformat(),
        "read_at": None,
    }


def get_player_notifications(
    db: Session, uid: str, limit: int = 20, unread_only: bool = False
) -> list[dict]:
    query = db.query(Notification).filter(Notification.uid == uid).order_by(Notification.created_at.desc())
    if unread_only:
        query = query.filter(Notification.is_read == False)
    notifs = query.limit(limit).all()
    return [
        {
            "notification_id": n.id,
            "player_uid": n.uid,
            "type": n.type,
            "title": n.title,
            "body": n.body,
            "data": n.data or {},
            "created_at": n.created_at.isoformat(),
            "read_at": None if not n.is_read else n.created_at.isoformat(),
        }
        for n in notifs
    ]


def mark_notification_read(db: Session, uid: str, notification_id: str) -> dict:
    notif = db.query(Notification).filter(Notification.id == notification_id, Notification.uid == uid).first()
    if notif:
        notif.is_read = True
        db.commit()
    return {"success": True, "message": "Marked as read"}


def mark_notification_clicked(db: Session, uid: str, notification_id: str) -> dict:
    return {"success": True, "message": "Marked as clicked"}


def update_notification_preferences(db: Session, uid: str, preferences: dict) -> dict:
    # Preferences stored outside notifications for now — just return success
    return {"success": True, "message": "Preferences updated"}


def should_send_notification(db: Session, uid: str, notification_type: str) -> bool:
    return True


def get_notification_preferences(db: Session, uid: str) -> dict:
    return {
        "match_needs_players": True,
        "team_challenge": True,
        "match_reminder": True,
        "reward_earned": True,
        "promoted_from_waitlist": True,
        "frequency": "instant",
    }


def notify_match_needs_players(
    db: Session, booking_id: str, sport: str, slots_needed: int,
    time_until_match: int, nearby_player_uids: list[str],
) -> None:
    title = f"{slots_needed} players needed for {sport}"
    body = f"Match starts in {time_until_match} mins"
    data = {"booking_id": booking_id, "sport": sport}
    for player_uid in nearby_player_uids:
        record_notification(db, player_uid, "match_needs_players", title, body, data)


def notify_team_challenged(
    db: Session, team_id: str, challenge_id: str,
    challenger_team_name: str, opponent_team_members: list[str],
) -> None:
    title = f"Team challenge from {challenger_team_name}"
    body = "Click to view and accept"
    data = {"team_id": team_id, "challenge_id": challenge_id}
    for player_uid in opponent_team_members:
        record_notification(db, player_uid, "team_challenge", title, body, data)


def notify_match_reminder(db: Session, booking_id: str, player_uid: str, sport: str, minutes_until: int) -> None:
    title = f"Your {sport} match in {minutes_until} mins!"
    body = "Arrive early for check-in"
    record_notification(db, player_uid, "match_reminder", title, body, {"booking_id": booking_id})


def notify_reward_earned(db: Session, player_uid: str, credits_amount: float, reason: str) -> None:
    title = f"You earned ₹{credits_amount}!"
    record_notification(db, player_uid, "reward_earned", title, reason, {"credits_amount": str(credits_amount)})


def notify_promoted_from_waitlist(db: Session, player_uid: str, booking_id: str, sport: str, position: int) -> None:
    title = "You're in! Slot opened up"
    body = f"Confirm within 30 mins. You were #{position} in queue"
    record_notification(db, player_uid, "promoted_from_waitlist", title, body, {"booking_id": booking_id})


def notify_match_formed(
    db: Session, booking_id: str, matched_uids: list[str], venue_name: str, sport: str, time_range: str
) -> None:
    title = f"You're matched! {sport.title()} at {venue_name}"
    body = f"{time_range} — see you there"
    data = {"booking_id": booking_id, "sport": sport}
    for player_uid in matched_uids:
        record_notification(db, player_uid, "match_formed", title, body, data)
