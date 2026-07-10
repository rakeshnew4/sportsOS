"""Notifications endpoints - Phase 4 (Growth Engine)."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.db import Client, get_db
from app.core.security import CurrentUser, get_current_user
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationResponse(BaseModel):
    """Notification object."""
    notification_id: str
    type: str
    title: str
    body: str
    data: dict
    created_at: str
    read_at: str | None = None
    clicked_at: str | None = None


class NotificationPreferencesRequest(BaseModel):
    """User notification preferences."""
    match_needs_players: bool = True
    team_challenge: bool = True
    match_reminder: bool = True
    reward_earned: bool = True
    promoted_from_waitlist: bool = True
    frequency: str = "instant"  # instant, hourly, daily, disabled
    quiet_hours_start: str | None = None  # HH:MM
    quiet_hours_end: str | None = None    # HH:MM


@router.get("/me")
def get_my_notifications(
    user: CurrentUser = Depends(get_current_user),
    db: Client = Depends(get_db),
    unread_only: bool = False,
    limit: int = 20,
) -> list[NotificationResponse]:
    """Get current user's notifications."""
    notifications = notification_service.get_player_notifications(
        db, user.uid, limit=limit, unread_only=unread_only
    )
    return [NotificationResponse(**n) for n in notifications]


@router.post("/me/{notification_id}/read")
def mark_as_read(
    notification_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Client = Depends(get_db),
) -> dict:
    """Mark notification as read."""
    return notification_service.mark_notification_read(db, user.uid, notification_id)


@router.post("/me/{notification_id}/clicked")
def mark_as_clicked(
    notification_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Client = Depends(get_db),
) -> dict:
    """Mark notification as clicked (for analytics)."""
    return notification_service.mark_notification_clicked(db, user.uid, notification_id)


@router.get("/me/preferences")
def get_notification_preferences(
    user: CurrentUser = Depends(get_current_user),
    db: Client = Depends(get_db),
) -> NotificationPreferencesRequest:
    """Get user's notification preferences."""
    prefs = notification_service.get_notification_preferences(db, user.uid)
    return NotificationPreferencesRequest(**prefs)


@router.patch("/me/preferences")
def update_notification_preferences(
    req: NotificationPreferencesRequest,
    user: CurrentUser = Depends(get_current_user),
    db: Client = Depends(get_db),
) -> dict:
    """Update user's notification preferences."""
    prefs_dict = req.dict(exclude_none=True)
    return notification_service.update_notification_preferences(db, user.uid, prefs_dict)
