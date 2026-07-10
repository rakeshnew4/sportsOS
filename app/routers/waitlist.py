"""Waitlist endpoints - Phase 4 (Growth Engine)."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.db import Client, get_db
from app.core.security import CurrentUser, get_current_user, require_venue_access
from app.services import waitlist_service

router = APIRouter(tags=["waitlist"])


class WaitlistEntry(BaseModel):
    """Waitlist entry."""
    player_uid: str
    position: int
    joined_at: str
    status: str


class WaitlistResponse(BaseModel):
    """Waitlist for a booking."""
    booking_id: str
    total_waiting: int
    queue: list[WaitlistEntry]


class MyWaitlistPosition(BaseModel):
    """My position on waitlist."""
    booking_id: str
    player_uid: str
    position: int
    status: str
    joined_at: str


class JoinWaitlistResponse(BaseModel):
    """Response when joining waitlist."""
    success: bool
    booking_id: str
    position: int
    message: str


# Join/Manage Waitlist

@router.post("/venues/{tenant_id}/bookings/{booking_id}/waitlist")
def join_waitlist(
    tenant_id: str,
    booking_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Client = Depends(get_db),
) -> JoinWaitlistResponse:
    """Join waitlist for a full match."""
    result = waitlist_service.join_waitlist(db, tenant_id, booking_id, user.uid)
    return JoinWaitlistResponse(**result)


@router.get("/venues/{tenant_id}/bookings/{booking_id}/waitlist")
def get_waitlist(
    tenant_id: str,
    booking_id: str,
    user: CurrentUser = Depends(require_venue_access),
    db: Client = Depends(get_db),
) -> WaitlistResponse:
    """Get waitlist for a booking (venue/staff only)."""
    result = waitlist_service.get_waitlist(db, tenant_id, booking_id)
    return WaitlistResponse(**result)


@router.get("/players/me/waitlist/{booking_id}")
def get_my_waitlist_position(
    booking_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Client = Depends(get_db),
) -> MyWaitlistPosition:
    """Get my position on waitlist for a booking."""
    tenant_id = waitlist_service.get_tenant_id_from_booking(db, booking_id)
    result = waitlist_service.get_my_waitlist_position(
        db, tenant_id=tenant_id,
        booking_id=booking_id,
        player_uid=user.uid
    )
    return MyWaitlistPosition(**result)


@router.post("/players/me/waitlist/{booking_id}/confirm")
def confirm_promotion(
    booking_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Client = Depends(get_db),
) -> dict:
    """Confirm promotion from waitlist (30-min window)."""
    tenant_id = waitlist_service.get_tenant_id_from_booking(db, booking_id)
    result = waitlist_service.confirm_promotion(
        db,
        tenant_id=tenant_id,
        booking_id=booking_id,
        player_uid=user.uid
    )
    return result


@router.post("/players/me/waitlist/{booking_id}/decline")
def decline_promotion(
    booking_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Client = Depends(get_db),
) -> dict:
    """Decline promotion, promote next player in queue."""
    tenant_id = waitlist_service.get_tenant_id_from_booking(db, booking_id)
    result = waitlist_service.decline_promotion(
        db,
        tenant_id=tenant_id,
        booking_id=booking_id,
        player_uid=user.uid
    )
    return result


@router.delete("/players/me/waitlist/{booking_id}")
def leave_waitlist(
    booking_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Client = Depends(get_db),
) -> dict:
    """Leave waitlist for a booking."""
    tenant_id = waitlist_service.get_tenant_id_from_booking(db, booking_id)
    result = waitlist_service.remove_from_waitlist(
        db,
        tenant_id=tenant_id,
        booking_id=booking_id,
        player_uid=user.uid
    )
    return result


# Admin: Manual promotion

@router.post("/venues/{tenant_id}/bookings/{booking_id}/waitlist/promote")
def promote_next_from_waitlist(
    tenant_id: str,
    booking_id: str,
    user: CurrentUser = Depends(require_venue_access),
    db: Client = Depends(get_db),
) -> dict:
    """Manually promote next player from waitlist (venue staff only)."""
    result = waitlist_service.promote_from_waitlist(db, tenant_id, booking_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No players waiting"
        )
    return result
