import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.orm import Booking, BookingParticipant
from app.models.booking import AvailabilityResponse, BookingCreateRequest, BookingResponse, SlotResponse, TimeRange
from app.services.court_service import get_court

ACTIVE_STATUSES = ("pending_payment", "confirmed")


def to_minutes(hhmm: str) -> int:
    hours, minutes = hhmm.split(":")
    return int(hours) * 60 + int(minutes)


def booking_to_response(b: Booking) -> BookingResponse:
    return BookingResponse(
        booking_id=b.booking_id,
        tenant_id=b.tenant_id,
        court_id=b.court_id,
        sport=b.sport,
        date=b.date,
        start_time=b.start_time,
        end_time=b.end_time,
        price=b.price,
        status=b.status,
        created_by=b.created_by,
        team_id=b.team_id,
        team_name=b.team_name,
        is_joinable=b.is_joinable,
        slots_total=b.slots_total,
        slots_open=b.slots_open,
    )


def get_availability(db: Session, tenant_id: str, court_id: str, date: str) -> AvailabilityResponse:
    court = get_court(db, tenant_id, court_id)
    existing = (
        db.query(Booking)
        .filter(
            Booking.tenant_id == tenant_id,
            Booking.court_id == court_id,
            Booking.date == date,
            Booking.status.in_(list(ACTIVE_STATUSES)),
        )
        .all()
    )
    booked_ranges = sorted(
        ((b.start_time, b.end_time) for b in existing),
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


def get_slots(db: Session, tenant_id: str, court_id: str, date: str, granularity: int = 30) -> list[SlotResponse]:
    court = get_court(db, tenant_id, court_id)
    availability = get_availability(db, tenant_id, court_id, date)
    open_ranges = [(to_minutes(r.start_time), to_minutes(r.end_time)) for r in availability.open_slots]

    use_dynamic = False
    try:
        from app.services.pricing_service import should_use_dynamic_pricing
        use_dynamic = should_use_dynamic_pricing(db, tenant_id, court_id)
    except ImportError:
        pass

    slots: list[SlotResponse] = []
    cursor = to_minutes(court.open_time)
    close = to_minutes(court.close_time)
    while cursor + granularity <= close:
        slot_start, slot_end = cursor, cursor + granularity
        available = any(slot_start >= r[0] and slot_end <= r[1] for r in open_ranges)
        price = None
        if available:
            hourly_rate = court.hourly_price
            if use_dynamic:
                from app.services.pricing_service import get_dynamic_price
                start_str = f"{slot_start // 60:02d}:{slot_start % 60:02d}"
                hourly_rate = get_dynamic_price(db, tenant_id, court_id, date, start_str, court.hourly_price)
            price = round(hourly_rate * (granularity / 60), 2)
        slots.append(
            SlotResponse(
                start_time=f"{slot_start // 60:02d}:{slot_start % 60:02d}",
                end_time=f"{slot_end // 60:02d}:{slot_end % 60:02d}",
                available=available,
                price=price,
            )
        )
        cursor += granularity
    return slots


def slot_overlaps_existing(
    db: Session, tenant_id: str, court_id: str, date: str, start_time: str, end_time: str
) -> bool:
    start_min, end_min = to_minutes(start_time), to_minutes(end_time)
    existing = (
        db.query(Booking)
        .filter(
            Booking.tenant_id == tenant_id,
            Booking.court_id == court_id,
            Booking.date == date,
            Booking.status.in_(list(ACTIVE_STATUSES)),
        )
        .all()
    )
    for b in existing:
        if start_min < to_minutes(b.end_time) and end_min > to_minutes(b.start_time):
            return True
    return False


def create_booking(db: Session, tenant_id: str, uid: str, req: BookingCreateRequest) -> BookingResponse:
    court = get_court(db, tenant_id, req.court_id)
    if not court.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Court is not active")

    start_min, end_min = to_minutes(req.start_time), to_minutes(req.end_time)
    if end_min <= start_min:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="end_time must be after start_time")
    if (end_min - start_min) < 60:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Minimum booking duration is 1 hour")
    if start_min < to_minutes(court.open_time) or end_min > to_minutes(court.close_time):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Requested time is outside court operating hours"
        )
    if slot_overlaps_existing(db, tenant_id, req.court_id, req.date, req.start_time, req.end_time):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slot overlaps an existing booking")

    hourly_rate = court.hourly_price
    try:
        from app.services.pricing_service import should_use_dynamic_pricing, get_dynamic_price
        if should_use_dynamic_pricing(db, tenant_id, req.court_id):
            hourly_rate = get_dynamic_price(db, tenant_id, req.court_id, req.date, req.start_time, court.hourly_price)
    except ImportError:
        pass

    price = round(hourly_rate * ((end_min - start_min) / 60), 2)

    from app.services.team_service import create_team
    team = create_team(db, uid, court.sport, req.team_name)

    booking = Booking(
        booking_id=uuid.uuid4().hex,
        tenant_id=tenant_id,
        court_id=req.court_id,
        sport=court.sport,
        date=req.date,
        start_time=req.start_time,
        end_time=req.end_time,
        price=price,
        status="confirmed",
        created_by=uid,
        team_id=team.team_id,
        team_name=team.team_name,
        is_joinable=False,
        slots_total=0,
        slots_open=0,
        created_at=datetime.now(timezone.utc),
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking_to_response(booking)


def list_venue_bookings(db: Session, tenant_id: str, date: str | None = None) -> list[BookingResponse]:
    query = db.query(Booking).filter(Booking.tenant_id == tenant_id)
    if date:
        query = query.filter(Booking.date == date)
    return [booking_to_response(b) for b in query.all()]


def get_booking(db: Session, tenant_id: str, booking_id: str) -> Booking:
    b = (
        db.query(Booking)
        .filter(Booking.booking_id == booking_id, Booking.tenant_id == tenant_id)
        .first()
    )
    if not b:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    return b


def list_my_bookings(db: Session, uid: str) -> list[BookingResponse]:
    bookings = db.query(Booking).filter(Booking.created_by == uid).all()
    return [booking_to_response(b) for b in bookings]


def list_bookings(db: Session, tenant_id: str) -> list[BookingResponse]:
    return list_venue_bookings(db, tenant_id)


def cancel_booking(db: Session, tenant_id: str, booking_id: str, uid: str, is_staff: bool) -> BookingResponse:
    booking = get_booking(db, tenant_id, booking_id)
    if booking.created_by != uid and not is_staff:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your booking")
    if booking.status in ("completed", "cancelled"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Booking already {booking.status}")
    booking.status = "cancelled"
    db.commit()

    try:
        from app.services import waitlist_service
        waitlist_service.promote_from_waitlist(db, tenant_id, booking_id)
    except Exception:
        pass

    return booking_to_response(booking)


def checkin_player(db: Session, tenant_id: str, booking_id: str, player_uid: str, requester_uid: str) -> dict:
    booking = get_booking(db, tenant_id, booking_id)
    existing = (
        db.query(BookingParticipant)
        .filter(BookingParticipant.booking_id == booking_id, BookingParticipant.uid == player_uid)
        .first()
    )
    if not existing:
        db.add(BookingParticipant(
            booking_id=booking_id,
            uid=player_uid,
            joined_at=datetime.now(timezone.utc),
        ))
        db.commit()
    return {"success": True, "message": f"Player {player_uid} checked in", "booking_id": booking_id}


def get_checkins(db: Session, tenant_id: str, booking_id: str) -> dict:
    get_booking(db, tenant_id, booking_id)
    participants = (
        db.query(BookingParticipant)
        .filter(BookingParticipant.booking_id == booking_id)
        .all()
    )
    checked_in = [p.uid for p in participants]
    return {
        "booking_id": booking_id,
        "checked_in_count": len(checked_in),
        "checked_in_players": checked_in,
    }


def complete_match(db: Session, tenant_id: str, booking_id: str, captain_uid: str) -> dict:
    booking = get_booking(db, tenant_id, booking_id)
    if booking.created_by != captain_uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only captain can complete match")

    checkins_data = get_checkins(db, tenant_id, booking_id)
    booking.status = "completed"
    db.commit()

    from app.services import rewards_service, team_service
    reward_amount = 10.0
    if booking.slots_open == 0:
        reward_amount += 20.0

    rewards_service.issue_reward(
        db, captain_uid, "match_completed", reward_amount,
        f"Completed {booking.sport} match", booking_id
    )

    if booking.team_id:
        try:
            team_service.record_team_match(
                db,
                team_id=booking.team_id,
                booking_id=booking_id,
                opponent_team_id="community",
                opponent_team_name="Community Players",
                result="win",
                player_count=checkins_data["checked_in_count"],
                venue_id=tenant_id,
            )
        except Exception:
            pass

    db.commit()

    return {
        "booking_id": booking_id,
        "status": "completed",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "players_checked_in": checkins_data["checked_in_count"],
        "total_players": booking.slots_total,
        "captain_rewards_earned": reward_amount,
        "message": f"Match completed! Captain earned {reward_amount} credits",
    }
