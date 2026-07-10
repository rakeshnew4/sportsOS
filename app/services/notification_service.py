"""
Notification service for Phase 4 (Growth Engine).

Handles all notifications:
- Match needs players
- Team challenges
- Match reminders
- Rewards earned
- Promotions from waitlist

Integration: Firebase Cloud Messaging (FCM)
"""

from datetime import datetime, timezone
import uuid
from typing import Literal

from fastapi import HTTPException, status
from app.core.db import Client, FieldFilter


NotificationType = Literal[
    "match_needs_players",
    "team_challenge",
    "match_reminder",
    "reward_earned",
    "promoted_from_waitlist",
    "slot_cancelled",
    "friend_activity",
]


def notifications_collection(db: Client, uid: str):
    """Get notifications subcollection for a player."""
    return db.collection("players").document(uid).collection("notifications")


def notification_preferences_collection(db: Client, uid: str):
    """Get notification preferences for a player."""
    return db.collection("players").document(uid).collection("preferences")


def record_notification(
    db: Client,
    player_uid: str,
    notification_type: NotificationType,
    title: str,
    body: str,
    data: dict | None = None,
    send_push: bool = True,
) -> dict:
    """Record a notification in database and queue for push (when FCM integrated)."""
    notification_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    notification = {
        "notification_id": notification_id,
        "player_uid": player_uid,
        "type": notification_type,
        "title": title,
        "body": body,
        "data": data or {},
        "created_at": now,
        "read_at": None,
        "clicked_at": None,
        "queued_for_push": send_push,
    }

    notifications_collection(db, player_uid).document(notification_id).set(notification)

    # TODO: Queue for Firebase Cloud Messaging push when integrated
    if send_push:
        queue_push_notification(db, player_uid, notification)

    return notification


def queue_push_notification(db: Client, player_uid: str, notification: dict) -> None:
    """Queue a notification for push delivery (Firebase Cloud Messaging)."""
    # TODO: Implement Firebase Cloud Messaging integration
    # This will be called when FCM is set up
    # For now, we store it in DB and process via background job
    push_queue = db.collection("push_queue").document(str(uuid.uuid4()))
    push_queue.set({
        "player_uid": player_uid,
        "notification_id": notification["notification_id"],
        "status": "queued",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "retry_count": 0,
    })


def get_notification_preferences(db: Client, uid: str) -> dict:
    """Get user's notification preferences."""
    prefs_doc = db.collection("players").document(uid).get()
    if prefs_doc.exists:
        data = prefs_doc.to_dict()
        return data.get("notification_preferences", {
            "match_needs_players": True,
            "team_challenge": True,
            "match_reminder": True,
            "reward_earned": True,
            "promoted_from_waitlist": True,
            "frequency": "instant",  # instant, hourly, daily, disabled
            "quiet_hours_start": None,  # e.g., "20:00"
            "quiet_hours_end": None,    # e.g., "08:00"
        })
    return {}


def should_send_notification(db: Client, uid: str, notification_type: NotificationType) -> bool:
    """Check if user wants this type of notification."""
    prefs = get_notification_preferences(db, uid)
    return prefs.get(notification_type, True)


# Phase 4 Notification Triggers

def notify_match_needs_players(
    db: Client,
    booking_id: str,
    sport: str,
    slots_needed: int,
    time_until_match: int,  # minutes
    nearby_player_uids: list[str],
) -> None:
    """Notify nearby players that a match needs players."""
    title = f"{slots_needed} players needed for {sport}"
    body = f"Match starts in {time_until_match} mins"
    data = {
        "booking_id": booking_id,
        "sport": sport,
        "slots_needed": str(slots_needed),
        "time_until_match": str(time_until_match),
    }

    for player_uid in nearby_player_uids:
        if should_send_notification(db, player_uid, "match_needs_players"):
            record_notification(
                db,
                player_uid,
                "match_needs_players",
                title,
                body,
                data,
            )


def notify_team_challenged(
    db: Client,
    team_id: str,
    challenge_id: str,
    challenger_team_name: str,
    opponent_team_members: list[str],
) -> None:
    """Notify team captains they've been challenged."""
    title = f"Team challenge from {challenger_team_name}"
    body = "Click to view and accept"
    data = {
        "team_id": team_id,
        "challenge_id": challenge_id,
        "challenger_team_name": challenger_team_name,
    }

    for player_uid in opponent_team_members:
        if should_send_notification(db, player_uid, "team_challenge"):
            record_notification(
                db,
                player_uid,
                "team_challenge",
                title,
                body,
                data,
            )


def notify_match_reminder(
    db: Client,
    booking_id: str,
    player_uid: str,
    sport: str,
    minutes_until: int,
) -> None:
    """Remind player their match starts soon."""
    title = f"Your {sport} match in {minutes_until} mins!"
    body = "Arrive early for check-in"
    data = {
        "booking_id": booking_id,
        "sport": sport,
    }

    if should_send_notification(db, player_uid, "match_reminder"):
        record_notification(
            db,
            player_uid,
            "match_reminder",
            title,
            body,
            data,
        )


def notify_reward_earned(
    db: Client,
    player_uid: str,
    credits_amount: float,
    reason: str,
) -> None:
    """Notify player they earned credits."""
    title = f"You earned ₹{credits_amount}!"
    body = reason
    data = {
        "credits_amount": str(credits_amount),
        "reason": reason,
    }

    if should_send_notification(db, player_uid, "reward_earned"):
        record_notification(
            db,
            player_uid,
            "reward_earned",
            title,
            body,
            data,
        )


def notify_promoted_from_waitlist(
    db: Client,
    player_uid: str,
    booking_id: str,
    sport: str,
    position: int,
) -> None:
    """Notify player they've been promoted from waitlist."""
    title = "You're in! Slot opened up"
    body = f"Confirm within 30 mins. You were #{position} in queue"
    data = {
        "booking_id": booking_id,
        "sport": sport,
        "action": "confirm_promotion",
    }

    if should_send_notification(db, player_uid, "promoted_from_waitlist"):
        record_notification(
            db,
            player_uid,
            "promoted_from_waitlist",
            title,
            body,
            data,
        )


def notify_slot_cancelled(
    db: Client,
    booking_id: str,
    affected_players: list[str],
) -> None:
    """Notify waitlist about cancellation (for auto-promotion)."""
    for player_uid in affected_players:
        # This triggers check for auto-promotion
        # Notification sent only if promoted
        pass


# Notification History & Analytics

def get_player_notifications(
    db: Client,
    uid: str,
    limit: int = 20,
    unread_only: bool = False,
) -> list[dict]:
    """Get player's notifications."""
    query = notifications_collection(db, uid).order_by(
        "created_at",
        direction="DESCENDING"
    )

    if unread_only:
        query = query.where(filter=FieldFilter("read_at", "==", None))

    notifications = []
    for doc in query.stream():
        notifications.append(doc.to_dict())

    return notifications[:limit]


def mark_notification_read(db: Client, uid: str, notification_id: str) -> dict:
    """Mark notification as read."""
    now = datetime.now(timezone.utc).isoformat()
    notifications_collection(db, uid).document(notification_id).update({
        "read_at": now,
    })
    return {"success": True, "message": "Marked as read"}


def mark_notification_clicked(db: Client, uid: str, notification_id: str) -> dict:
    """Mark notification as clicked (for analytics)."""
    now = datetime.now(timezone.utc).isoformat()
    notifications_collection(db, uid).document(notification_id).update({
        "clicked_at": now,
    })
    return {"success": True, "message": "Marked as clicked"}


def update_notification_preferences(
    db: Client,
    uid: str,
    preferences: dict,
) -> dict:
    """Update user's notification preferences."""
    db.collection("players").document(uid).set(
        {"notification_preferences": preferences},
        merge=True
    )
    return {"success": True, "message": "Preferences updated"}
