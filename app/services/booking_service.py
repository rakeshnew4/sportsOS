from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.core.db import Client, FieldFilter
from app.models.booking import AvailabilityResponse, BookingCreateRequest, BookingResponse, TimeRange
from app.services.court_service import get_court

ACTIVE_STATUSES = ("pending_payment", "confirmed")


def to_minutes(hhmm: str) -> int:
    hours, minutes = hhmm.split(":")
    return int(hours) * 60 + int(minutes)


def bookings_ref(db: Client, tenant_id: str):
    return db.collection("tenants").document(tenant_id).collection("bookings")


def booking_to_response(tenant_id: str, booking_id: str, data: dict) -> BookingResponse:
    return BookingResponse(
        booking_id=booking_id,
        tenant_id=tenant_id,
        court_id=data["court_id"],
        sport=data["sport"],
        date=data["date"],
        start_time=data["start_time"],
        end_time=data["end_time"],
        price=data["price"],
        status=data["status"],
        created_by=data["created_by"],
        team_id=data.get("team_id"),
        team_name=data.get("team_name"),
        is_joinable=data.get("is_joinable", False),
        slots_total=data.get("slots_total", 0),
        slots_open=data.get("slots_open", 0),
    )


def get_availability(db: Client, tenant_id: str, court_id: str, date: str) -> AvailabilityResponse:
    court = get_court(db, tenant_id, court_id)
    existing = (
        bookings_ref(db, tenant_id)
        .where(filter=FieldFilter("court_id", "==", court_id))
        .where(filter=FieldFilter("date", "==", date))
        .where(filter=FieldFilter("status", "in", list(ACTIVE_STATUSES)))
        .stream()
    )
    booked_ranges = sorted(
        ((doc.to_dict()["start_time"], doc.to_dict()["end_time"]) for doc in existing),
        key=lambda r: to_minutes(r[0]),
    )

    open_ranges: list[TimeRange] = []
    cursor = court.open_time
    for start, end in booked_ranges:
        if to_minutes(cursor) < to_minutes(start):
            open_ranges.append(TimeRange(start_time=cursor, end_time=start))
        cursor = end
    if to_minutes(cursor) < to_minutes(court.close_time):
        open_ranges.append(TimeRange(start_time=cursor, end_time=court.close_time))

    return AvailabilityResponse(
        court_id=court_id,
        date=date,
        open_slots=open_ranges,
        booked_slots=[TimeRange(start_time=s, end_time=e) for s, e in booked_ranges],
    )


def slot_overlaps_existing(db: Client, tenant_id: str, court_id: str, date: str, start_time: str, end_time: str) -> bool:
    start_min, end_min = to_minutes(start_time), to_minutes(end_time)
    existing = (
        bookings_ref(db, tenant_id)
        .where(filter=FieldFilter("court_id", "==", court_id))
        .where(filter=FieldFilter("date", "==", date))
        .where(filter=FieldFilter("status", "in", list(ACTIVE_STATUSES)))
        .stream()
    )
    for doc in existing:
        other = doc.to_dict()
        if start_min < to_minutes(other["end_time"]) and end_min > to_minutes(other["start_time"]):
            return True
    return False


def create_booking(db: Client, tenant_id: str, uid: str, req: BookingCreateRequest) -> BookingResponse:
    court = get_court(db, tenant_id, req.court_id)
    if not court.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Court is not active")

    start_min, end_min = to_minutes(req.start_time), to_minutes(req.end_time)
    if end_min <= start_min:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="end_time must be after start_time")

    duration_minutes = end_min - start_min
    if duration_minutes < 60:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Minimum booking duration is 1 hour")

    if start_min < to_minutes(court.open_time) or end_min > to_minutes(court.close_time):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Requested time is outside court operating hours"
        )

    if slot_overlaps_existing(db, tenant_id, req.court_id, req.date, req.start_time, req.end_time):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slot overlaps an existing booking")

    duration_hours = (end_min - start_min) / 60

    # Use dynamic pricing if enabled for this court
    hourly_rate = court.hourly_price
    try:
        from app.services.pricing_service import should_use_dynamic_pricing, get_dynamic_price
        if should_use_dynamic_pricing(db, tenant_id, req.court_id):
            hourly_rate = get_dynamic_price(db, tenant_id, req.court_id, req.date, req.start_time, court.hourly_price)
    except ImportError:
        pass

    price = round(hourly_rate * duration_hours, 2)

    # Create a team for this booking
    from app.services.team_service import create_team
    team = create_team(db, uid, court.sport, req.team_name)

    booking_ref = bookings_ref(db, tenant_id).document()
    data = {
        "court_id": req.court_id,
        "sport": court.sport,
        "date": req.date,
        "start_time": req.start_time,
        "end_time": req.end_time,
        "price": price,
        "status": "confirmed",
        "created_by": uid,
        "team_id": team.team_id,
        "team_name": team.team_name,
        "is_joinable": False,
        "slots_total": 0,
        "slots_open": 0,
        "tenant_name": None,
        "geo": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    booking_ref.set(data)
    return booking_to_response(tenant_id, booking_ref.id, data)


def list_venue_bookings(db: Client, tenant_id: str, date: str | None = None) -> list[BookingResponse]:
    query = bookings_ref(db, tenant_id)
    if date:
        query = query.where(filter=FieldFilter("date", "==", date))
    return [booking_to_response(tenant_id, doc.id, doc.to_dict()) for doc in query.stream()]


def get_booking(db: Client, tenant_id: str, booking_id: str):
    doc = bookings_ref(db, tenant_id).document(booking_id).get()
    if not doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    return doc


def list_my_bookings(db: Client, uid: str) -> list[BookingResponse]:
    docs = db.collection_group("bookings").where(filter=FieldFilter("created_by", "==", uid)).stream()
    results = []
    for doc in docs:
        tenant_id = doc.reference.parent.parent.id
        results.append(booking_to_response(tenant_id, doc.id, doc.to_dict()))
    return results


def list_bookings(db: Client, tenant_id: str) -> list[BookingResponse]:
    """Get all bookings for a venue (across all dates)."""
    docs = bookings_ref(db, tenant_id).stream()
    results = []
    for doc in docs:
        results.append(booking_to_response(tenant_id, doc.id, doc.to_dict()))
    return results


def cancel_booking(db: Client, tenant_id: str, booking_id: str, uid: str, is_staff: bool) -> BookingResponse:
    booking_ref = bookings_ref(db, tenant_id).document(booking_id)
    doc = booking_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    data = doc.to_dict()
    if data["created_by"] != uid and not is_staff:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your booking")
    if data["status"] in ("completed", "cancelled"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Booking already {data['status']}")
    booking_ref.update({"status": "cancelled"})
    data["status"] = "cancelled"

    # Auto-promote from waitlist when slot opens (Phase 4)
    try:
        from app.services import waitlist_service
        promoted = waitlist_service.promote_from_waitlist(db, tenant_id, booking_id)
        if promoted:
            # Next player gets promoted automatically
            # They receive notification with 30-min confirmation window
            pass
    except Exception:
        # Don't block cancellation if waitlist fails
        pass

    return booking_to_response(tenant_id, booking_id, data)


def checkin_player(db: Client, tenant_id: str, booking_id: str, player_uid: str, requester_uid: str) -> dict:
    """Check in a player to a match (QR code scan or manual)."""
    booking_doc = bookings_ref(db, tenant_id).document(booking_id).get()
    if not booking_doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    booking_data = booking_doc.to_dict()

    # Get check-in collection for this booking
    checkins = (
        bookings_ref(db, tenant_id)
        .document(booking_id)
        .collection("checkins")
    )

    # Record check-in
    checkins.document(player_uid).set({
        "player_uid": player_uid,
        "checked_in_at": datetime.now(timezone.utc).isoformat(),
    })

    return {
        "success": True,
        "message": f"Player {player_uid} checked in",
        "booking_id": booking_id,
    }


def get_checkins(db: Client, tenant_id: str, booking_id: str) -> dict:
    """Get check-in status for all players in a match."""
    booking_doc = bookings_ref(db, tenant_id).document(booking_id).get()
    if not booking_doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    checkins = (
        bookings_ref(db, tenant_id)
        .document(booking_id)
        .collection("checkins")
        .stream()
    )

    checked_in_players = []
    for doc in checkins:
        checked_in_players.append(doc.id)

    return {
        "booking_id": booking_id,
        "checked_in_count": len(checked_in_players),
        "checked_in_players": checked_in_players,
    }


def complete_match(db: Client, tenant_id: str, booking_id: str, captain_uid: str) -> dict:
    """Mark match as completed (after QR check-ins are done). Triggers reward issuance."""
    booking_ref = bookings_ref(db, tenant_id).document(booking_id)
    booking_doc = booking_ref.get()
    if not booking_doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    booking_data = booking_doc.to_dict()

    # Verify captain
    if booking_data["created_by"] != captain_uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only captain can complete match")

    # Get check-ins
    checkins_data = get_checkins(db, tenant_id, booking_id)

    # Mark booking as completed
    booking_ref.update({
        "status": "completed",
        "completed_at": datetime.now(timezone.utc).isoformat(),
    })

    # Issue captain reward
    from app.services import rewards_service, team_service
    reward_amount = 10.0  # Base reward for completing match

    # Add bonus if all slots filled
    if booking_data.get("slots_open", 0) == 0:
        reward_amount += 20.0

    rewards_service.issue_reward(
        db, captain_uid, "match_completed", reward_amount,
        f"Completed {booking_data['sport']} match",
        booking_id
    )

    # Record match in team history if team exists
    team_id = booking_data.get("team_id")
    if team_id:
        try:
            team_service.record_team_match(
                db,
                team_id=team_id,
                booking_id=booking_id,
                opponent_team_id="community",
                opponent_team_name="Community Players",
                result="win",
                player_count=checkins_data["checked_in_count"],
                venue_id=tenant_id
            )
        except Exception:
            pass

    return {
        "booking_id": booking_id,
        "status": "completed",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "players_checked_in": checkins_data["checked_in_count"],
        "total_players": booking_data.get("slots_total", 0),
        "captain_rewards_earned": reward_amount,
        "message": f"Match completed! Captain earned {reward_amount} credits",
    }
