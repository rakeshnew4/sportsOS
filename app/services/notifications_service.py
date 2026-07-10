"""In-app notifications system — short-signature helpers used by matchmaking_service.py
and the Streamlit demo UI.

This is a thin compatibility layer over notification_service.py: both modules used to
write into players/{uid}/notifications with two different, incompatible schemas (one
used a boolean `read` field, the other a `read_at` timestamp; one had no `notification_id`
field). That split meant notifications created here were invisible to the FastAPI
GET /notifications/me endpoint (pydantic validation error on the missing field) and
notifications created via notification_service (waitlist promotion, rewards, match
reminders, team challenges) never showed up in the Streamlit notification bell. Routing
everything through notification_service.record_notification keeps a single schema so
every producer/consumer stays interoperable.
"""

from app.core.db import Client
from app.services import notification_service


def create_notification(
    db: Client,
    uid: str,
    title: str,
    body: str,
    notification_type: str,
    data: dict = None,
) -> str:
    """Create a notification for a player."""
    record = notification_service.record_notification(
        db, uid, notification_type, title, body, data, send_push=False
    )
    return record["notification_id"]


def get_unread_notifications(db: Client, uid: str, limit: int = 10) -> list[dict]:
    """Get unread notifications for a player, most recent first."""
    notifications = notification_service.get_player_notifications(
        db, uid, limit=limit, unread_only=True
    )
    return [
        {
            "id": n["notification_id"],
            "title": n["title"],
            "body": n["body"],
            "type": n["type"],
            "data": n.get("data", {}),
            "created_at": n["created_at"],
            "read": n.get("read_at") is not None,
        }
        for n in notifications
    ]


def mark_as_read(db: Client, uid: str, notification_id: str) -> None:
    """Mark a notification as read."""
    notification_service.mark_notification_read(db, uid, notification_id)


def delete_notification(db: Client, uid: str, notification_id: str) -> None:
    """Delete a notification."""
    notification_service.notifications_collection(db, uid).document(notification_id).delete()


# Streamlit's preference checkboxes use display labels; notification_service.
# should_send_notification gates on the snake_case NotificationType values.
PREFERENCE_KEY_MAP = {
    "Match Needs Players": "match_needs_players",
    "Waitlist Promotion": "promoted_from_waitlist",
    "Team Challenges": "team_challenge",
    "Match Reminders": "match_reminder",
    "Rewards Earned": "reward_earned",
}


def update_notification_preferences(db: Client, uid: str, preferences: dict) -> dict:
    """Update a player's notification preferences (accepts display-label or snake_case keys)."""
    mapped = {PREFERENCE_KEY_MAP.get(k, k): v for k, v in preferences.items()}
    return notification_service.update_notification_preferences(db, uid, mapped)


def notify_match_formed(
    db: Client, booking_id: str, matched_uids: list[str], venue_name: str, sport: str, time_slot: str
) -> None:
    """Notify all matched players that their queue formed a match."""
    for uid in matched_uids:
        create_notification(
            db,
            uid,
            title="Match formed!",
            body=f"Your {sport} queue matched! Game at {venue_name} {time_slot}",
            notification_type="match_formed",
            data={"booking_id": booking_id, "sport": sport, "venue": venue_name},
        )


def notify_queue_filling(
    db: Client, queued_uids: list[str], current_count: int, min_count: int, sport: str, time_slot: str
) -> None:
    """Notify players in queue when more players join."""
    for uid in queued_uids:
        if current_count < min_count:
            pct = int((current_count / min_count) * 100)
            create_notification(
                db,
                uid,
                title=f"Match filling: {current_count}/{min_count}",
                body=f"{pct}% full — {min_count - current_count} more player(s) needed for {sport} at {time_slot}",
                notification_type="match_filling",
                data={"current_count": current_count, "min_count": min_count, "sport": sport},
            )


def notify_recommendation(db: Client, uid: str, sport: str, venue: str, time_slot: str, reason: str) -> None:
    """Notify a player about a personalized match recommendation."""
    create_notification(
        db,
        uid,
        title=f"{sport} match available!",
        body=f"Players like you are queuing {sport} at {venue} {time_slot} — {reason}",
        notification_type="recommendation",
        data={"sport": sport, "venue": venue, "time": time_slot},
    )


def notify_booking_reminder(db: Client, uid: str, sport: str, venue: str, time_slot: str, minutes_until: int) -> None:
    """Remind a player about an upcoming booking."""
    create_notification(
        db,
        uid,
        title="Match starting soon!",
        body=f"Your {sport} booking at {venue} starts in {minutes_until} minutes ({time_slot})",
        notification_type="booking_reminder",
        data={"sport": sport, "venue": venue, "minutes_until": minutes_until},
    )


def notify_with_llm(db: Client, uid: str, event_type: str, event_data: dict) -> str:
    """
    Create an engaging notification using LLM.
    Fallback to generic message if LLM fails.

    Args:
        uid: Player ID
        event_type: Type of event (match_formed, booking_reminder, etc)
        event_data: Dict with event details

    Returns:
        Notification ID
    """
    try:
        from app.services.llm_service import generate_notification_message
        message = generate_notification_message(event_type, event_data)
        return create_notification(
            db,
            uid,
            title=message.get("title", "SportsOS Update"),
            body=message.get("body", "Check your match!"),
            notification_type=event_type,
            data=event_data,
        )
    except Exception as e:
        print(f"LLM notification failed: {e}, using fallback")
        # Fallback to generic message
        fallback_messages = {
            "match_formed": ("🎉 Match formed!", "Your match is confirmed! Time to play."),
            "booking_reminder": ("⏰ Match reminder", "Your match is starting soon!"),
            "team_invitation": ("🎽 Team invitation", "You've been invited to join a team!"),
        }
        title, body = fallback_messages.get(event_type, ("SportsOS Update", "Check your match!"))
        return create_notification(db, uid, title, body, event_type, event_data)
