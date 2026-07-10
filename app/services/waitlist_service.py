"""
Waiting list service for Phase 4 (Growth Engine).

Handles full matches: converts "sorry, full" into "join queue" → auto-promotion on cancellation.
"""

from datetime import datetime, timezone
import uuid

from fastapi import HTTPException, status
from app.core.db import Client, FieldFilter


def get_tenant_id_from_booking(db: Client, booking_id: str) -> str:
    """Extract tenant_id from a booking by searching all tenants."""
    for tenant_doc in db.collection("tenants").stream():
        tenant_id = tenant_doc.id
        booking_doc = (
            db.collection("tenants")
            .document(tenant_id)
            .collection("bookings")
            .document(booking_id)
            .get()
        )
        if booking_doc.exists:
            return tenant_id
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")


def waitlist_collection(db: Client, tenant_id: str, booking_id: str):
    """Get waitlist for a booking."""
    return (
        db.collection("tenants")
        .document(tenant_id)
        .collection("bookings")
        .document(booking_id)
        .collection("waitlist")
    )


def join_waitlist(
    db: Client,
    tenant_id: str,
    booking_id: str,
    player_uid: str,
) -> dict:
    """Add player to waitlist for a full match."""
    # Verify booking exists
    booking_doc = (
        db.collection("tenants")
        .document(tenant_id)
        .collection("bookings")
        .document(booking_id)
        .get()
    )
    if not booking_doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    # Check if already on waitlist
    existing = waitlist_collection(db, tenant_id, booking_id).document(player_uid).get()
    if existing.exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already on waitlist")

    # Get current waitlist position
    waitlist_docs = list(waitlist_collection(db, tenant_id, booking_id).stream())
    position = len(waitlist_docs) + 1

    # Add to waitlist
    now = datetime.now(timezone.utc).isoformat()
    entry = {
        "player_uid": player_uid,
        "position": position,
        "joined_at": now,
        "status": "waiting",  # waiting, promoted, accepted, declined
    }

    waitlist_collection(db, tenant_id, booking_id).document(player_uid).set(entry)

    return {
        "success": True,
        "booking_id": booking_id,
        "position": position,
        "message": f"You've joined the waitlist at position {position}",
    }


def get_waitlist(
    db: Client,
    tenant_id: str,
    booking_id: str,
) -> dict:
    """Get waitlist for a booking."""
    waitlist = []
    for doc in waitlist_collection(db, tenant_id, booking_id).stream():
        waitlist.append(doc.to_dict())

    # Sort by position
    waitlist.sort(key=lambda x: x["position"])

    return {
        "booking_id": booking_id,
        "total_waiting": len(waitlist),
        "queue": waitlist,
    }


def get_my_waitlist_position(
    db: Client,
    tenant_id: str,
    booking_id: str,
    player_uid: str,
) -> dict:
    """Get player's position on waitlist."""
    # If tenant_id not provided, find it from booking
    if not tenant_id or tenant_id == "":
        booking_doc = db.collection_group("bookings").document(booking_id).get()
        if not booking_doc.exists:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
        # Extract tenant_id from reference path
        tenant_id = booking_doc.reference.parent.parent.id

    entry_doc = waitlist_collection(db, tenant_id, booking_id).document(player_uid).get()
    if not entry_doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not on waitlist")

    entry = entry_doc.to_dict()
    return {
        "booking_id": booking_id,
        "player_uid": player_uid,
        "position": entry["position"],
        "status": entry["status"],
        "joined_at": entry["joined_at"],
    }


def promote_from_waitlist(
    db: Client,
    tenant_id: str,
    booking_id: str,
) -> dict | None:
    """Promote next player from waitlist (call when slot opens)."""
    # Get first waiting player
    waiting_players = []
    for doc in waitlist_collection(db, tenant_id, booking_id).stream():
        data = doc.to_dict()
        if data["status"] == "waiting":
            waiting_players.append(data)

    if not waiting_players:
        return None

    # Sort by position and promote first
    waiting_players.sort(key=lambda x: x["position"])
    promoted_player = waiting_players[0]
    player_uid = promoted_player["player_uid"]

    # Update status to promoted
    now = datetime.now(timezone.utc).isoformat()
    waitlist_collection(db, tenant_id, booking_id).document(player_uid).update({
        "status": "promoted",
        "promoted_at": now,
        "expires_at": now,  # 30-min window to confirm
    })

    # Send notification
    booking_doc = (
        db.collection("tenants")
        .document(tenant_id)
        .collection("bookings")
        .document(booking_id)
        .get()
    )
    sport = booking_doc.to_dict().get("sport", "match") if booking_doc.exists else "match"

    from app.services import notification_service
    notification_service.notify_promoted_from_waitlist(
        db,
        player_uid,
        booking_id,
        sport=sport,
        position=promoted_player["position"],
    )

    return {
        "promoted_player_uid": player_uid,
        "position": promoted_player["position"],
        "message": f"Promoted player at position {promoted_player['position']}",
    }


def confirm_promotion(
    db: Client,
    tenant_id: str,
    booking_id: str,
    player_uid: str,
) -> dict:
    """Player confirms they want the promoted slot."""
    entry_doc = waitlist_collection(db, tenant_id, booking_id).document(player_uid).get()
    if not entry_doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not on waitlist")

    entry = entry_doc.to_dict()
    if entry["status"] != "promoted":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not in promoted state"
        )

    # Update status to accepted
    waitlist_collection(db, tenant_id, booking_id).document(player_uid).update({
        "status": "accepted",
        "accepted_at": datetime.now(timezone.utc).isoformat(),
    })

    # Add player to booking
    # TODO: Implement in booking_service
    # booking_service.add_player_to_booking(db, tenant_id, booking_id, player_uid)

    return {
        "success": True,
        "message": "You're in! Slot confirmed",
        "booking_id": booking_id,
    }


def decline_promotion(
    db: Client,
    tenant_id: str,
    booking_id: str,
    player_uid: str,
) -> dict:
    """Player declines promoted slot, promote next."""
    entry_doc = waitlist_collection(db, tenant_id, booking_id).document(player_uid).get()
    if not entry_doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not on waitlist")

    # Update status to declined
    waitlist_collection(db, tenant_id, booking_id).document(player_uid).update({
        "status": "declined",
        "declined_at": datetime.now(timezone.utc).isoformat(),
    })

    # Promote next player
    promote_from_waitlist(db, tenant_id, booking_id)

    return {
        "success": True,
        "message": "Declined. Next player promoted",
    }


def remove_from_waitlist(
    db: Client,
    tenant_id: str,
    booking_id: str,
    player_uid: str,
) -> dict:
    """Remove player from waitlist."""
    entry_doc = waitlist_collection(db, tenant_id, booking_id).document(player_uid).get()
    if not entry_doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not on waitlist")

    waitlist_collection(db, tenant_id, booking_id).document(player_uid).delete()

    return {
        "success": True,
        "message": "Removed from waitlist",
    }
