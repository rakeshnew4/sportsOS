"""Waiting list service — PostgreSQL-backed."""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.orm import Booking, Waitlist


def join_waitlist(db: Session, tenant_id: str, booking_id: str, player_uid: str) -> dict:
    booking = db.query(Booking).filter(Booking.booking_id == booking_id, Booking.tenant_id == tenant_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    existing = (
        db.query(Waitlist)
        .filter(Waitlist.booking_id == booking_id, Waitlist.uid == player_uid)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already on waitlist")
    position = db.query(Waitlist).filter(Waitlist.booking_id == booking_id).count() + 1
    entry = Waitlist(
        tenant_id=tenant_id,
        booking_id=booking_id,
        uid=player_uid,
        joined_at=datetime.now(timezone.utc),
        status="waiting",
    )
    db.add(entry)
    db.commit()
    return {"success": True, "booking_id": booking_id, "position": position, "message": f"Joined waitlist at position {position}"}


def get_waitlist(db: Session, tenant_id: str, booking_id: str) -> dict:
    entries = (
        db.query(Waitlist)
        .filter(Waitlist.booking_id == booking_id)
        .order_by(Waitlist.joined_at)
        .all()
    )
    queue = [{"player_uid": e.uid, "position": i + 1, "status": e.status, "joined_at": e.joined_at.isoformat()} for i, e in enumerate(entries)]
    return {"booking_id": booking_id, "total_waiting": len(queue), "queue": queue}


def get_my_waitlist_position(db: Session, tenant_id: str, booking_id: str, player_uid: str) -> dict:
    entries = (
        db.query(Waitlist)
        .filter(Waitlist.booking_id == booking_id)
        .order_by(Waitlist.joined_at)
        .all()
    )
    for i, e in enumerate(entries):
        if e.uid == player_uid:
            return {"booking_id": booking_id, "player_uid": player_uid, "position": i + 1, "status": e.status, "joined_at": e.joined_at.isoformat()}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not on waitlist")


def promote_from_waitlist(db: Session, tenant_id: str, booking_id: str) -> dict | None:
    waiting = (
        db.query(Waitlist)
        .filter(Waitlist.booking_id == booking_id, Waitlist.status == "waiting")
        .order_by(Waitlist.joined_at)
        .first()
    )
    if not waiting:
        return None
    waiting.status = "promoted"
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    sport = booking.sport if booking else "match"

    from app.services import notification_service
    notification_service.notify_promoted_from_waitlist(db, waiting.uid, booking_id, sport=sport, position=1)
    db.commit()
    return {"promoted_player_uid": waiting.uid}


def confirm_promotion(db: Session, tenant_id: str, booking_id: str, player_uid: str) -> dict:
    entry = db.query(Waitlist).filter(Waitlist.booking_id == booking_id, Waitlist.uid == player_uid).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not on waitlist")
    if entry.status != "promoted":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not in promoted state")
    entry.status = "accepted"
    db.commit()
    return {"success": True, "message": "You're in! Slot confirmed", "booking_id": booking_id}


def decline_promotion(db: Session, tenant_id: str, booking_id: str, player_uid: str) -> dict:
    entry = db.query(Waitlist).filter(Waitlist.booking_id == booking_id, Waitlist.uid == player_uid).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not on waitlist")
    entry.status = "declined"
    db.commit()
    promote_from_waitlist(db, tenant_id, booking_id)
    return {"success": True, "message": "Declined. Next player promoted"}


def get_tenant_id_from_booking(db: Session, booking_id: str) -> str:
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    return booking.tenant_id


def remove_from_waitlist(db: Session, tenant_id: str, booking_id: str, player_uid: str) -> dict:
    entry = db.query(Waitlist).filter(Waitlist.booking_id == booking_id, Waitlist.uid == player_uid).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not on waitlist")
    db.delete(entry)
    db.commit()
    return {"success": True, "message": "Removed from waitlist"}
