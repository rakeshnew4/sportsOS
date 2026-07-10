from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.orm import Booking, BookingParticipant, Wallet, WalletTransaction
from app.models.booking import BookingResponse
from app.models.match import MatchResponse, OpenToCommunityRequest, ParticipantResponse
from app.models.venue import GeoPoint
from app.services.booking_service import booking_to_response, get_booking
from app.services.venue_service import get_venue
from app.services.wallet_service import debit_wallet, credit_wallet
import uuid


def open_to_community(
    db: Session, tenant_id: str, booking_id: str, uid: str, req: OpenToCommunityRequest
) -> BookingResponse:
    booking = get_booking(db, tenant_id, booking_id)
    if booking.created_by != uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the captain who booked this slot can open it")
    if booking.status != "confirmed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only confirmed bookings can be opened to the community")
    if req.slots_open < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="slots_open must be at least 1")

    venue = get_venue(db, tenant_id)
    booking.is_joinable = True
    booking.slots_total = req.slots_open
    booking.slots_open = req.slots_open
    booking.tenant_name = venue.name
    booking.geo_lat = venue.geo.lat
    booking.geo_lng = venue.geo.lng
    db.commit()
    db.refresh(booking)
    return booking_to_response(booking)


def discover_matches(db: Session, sport: str | None = None, date: str | None = None) -> list[MatchResponse]:
    query = (
        db.query(Booking)
        .filter(
            Booking.is_joinable == True,
            Booking.status == "confirmed",
            Booking.slots_open > 0,
        )
    )
    if sport:
        query = query.filter(Booking.sport == sport)
    if date:
        query = query.filter(Booking.date == date)

    results = []
    for b in query.all():
        base = booking_to_response(b)
        results.append(
            MatchResponse(
                **base.model_dump(),
                tenant_name=b.tenant_name or "",
                geo=GeoPoint(lat=b.geo_lat or 0.0, lng=b.geo_lng or 0.0),
            )
        )
    return results


def join_match(db: Session, tenant_id: str, booking_id: str, uid: str) -> BookingResponse:
    booking = get_booking(db, tenant_id, booking_id)
    captain_uid = booking.created_by

    if captain_uid == uid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You already own this booking")
    if not booking.is_joinable or booking.status != "confirmed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This match is not open to join")
    if booking.slots_open <= 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No open slots left")

    existing = (
        db.query(BookingParticipant)
        .filter(BookingParticipant.booking_id == booking_id, BookingParticipant.uid == uid)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already joined this match")

    slots_total = booking.slots_total or 1
    price_per_slot = round(booking.price / slots_total, 2)

    # Debit joiner, credit captain — both wallet ops within same transaction
    debit_wallet(db, uid, price_per_slot, "Joined a community match", booking_id)
    credit_wallet(db, captain_uid, price_per_slot, "Player joined your open match", booking_id)

    booking.slots_open -= 1
    db.add(BookingParticipant(
        booking_id=booking_id,
        uid=uid,
        joined_at=datetime.now(timezone.utc),
    ))

    # Add to team if exists
    if booking.team_id:
        from app.services.team_service import add_team_member
        try:
            add_team_member(db, booking.team_id, uid)
        except HTTPException:
            pass

    db.commit()
    db.refresh(booking)
    return booking_to_response(booking)


def list_participants(db: Session, tenant_id: str, booking_id: str) -> list[ParticipantResponse]:
    get_booking(db, tenant_id, booking_id)
    participants = (
        db.query(BookingParticipant)
        .filter(BookingParticipant.booking_id == booking_id)
        .all()
    )
    return [
        ParticipantResponse(
            uid=p.uid,
            display_name=p.display_name,
            joined_at=p.joined_at.isoformat(),
        )
        for p in participants
    ]
