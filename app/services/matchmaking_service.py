"""True "Join Match" — PUBG-style matchmaking.

Players individually queue for a specific open court slot. Once enough of
them are queued for the same slot, the system forms a real booking, splits
the cost, and debits each matched player's wallet.
"""

from datetime import datetime, timezone
import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.orm import Booking, BookingParticipant, MatchRequest, User, Wallet, WalletTransaction
from app.models.matchmaking import MatchRequestCreate, MatchRequestResponse
from app.services.booking_service import slot_overlaps_existing, to_minutes
from app.services.court_service import get_court
from app.services import notification_service

MIN_PLAYERS = {
    "badminton": 4,
    "tennis": 2,
    "table_tennis": 2,
    "cricket": 10,
    "football": 10,
    "volleyball": 6,
    "basketball": 6,
}
DEFAULT_MIN_PLAYERS = 4


def _min_players_for(sport: str) -> int:
    return MIN_PLAYERS.get(sport, DEFAULT_MIN_PLAYERS)


def _to_response(
    mr: MatchRequest, current_count: int, tenant_name: str | None = None, court_name: str | None = None
) -> MatchRequestResponse:
    return MatchRequestResponse(
        request_id=mr.request_id,
        tenant_id=mr.tenant_id,
        court_id=mr.court_id,
        sport=mr.sport,
        date=mr.date,
        start_time=mr.start_time,
        end_time=mr.end_time,
        uid=mr.uid,
        status=mr.status,
        min_players=mr.min_players,
        current_count=current_count,
        matched_booking_id=mr.matched_booking_id,
        tenant_name=tenant_name,
        court_name=court_name,
    )


def _waiting_requests_for_slot(
    db: Session, tenant_id: str, court_id: str, date: str, start_time: str, end_time: str
) -> list[MatchRequest]:
    return (
        db.query(MatchRequest)
        .filter(
            MatchRequest.tenant_id == tenant_id,
            MatchRequest.court_id == court_id,
            MatchRequest.date == date,
            MatchRequest.start_time == start_time,
            MatchRequest.end_time == end_time,
            MatchRequest.status == "waiting",
        )
        .order_by(MatchRequest.created_at)
        .all()
    )


def _form_match(
    db: Session,
    waiting: list[MatchRequest],
    tenant_id: str,
    court_id: str,
    sport: str,
    date: str,
    start_time: str,
    end_time: str,
    price: float,
    team_id: str,
    tenant_name: str | None = None,
) -> str | None:
    # Verify all still waiting and have enough balance
    share = round(price / len(waiting), 2)
    for mr in waiting:
        db.refresh(mr)
        if mr.status != "waiting":
            return None
        wallet = db.query(Wallet).filter(Wallet.uid == mr.uid).with_for_update().first()
        if not wallet or wallet.balance < share:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One of the matched players doesn't have enough wallet balance",
            )

    now = datetime.now(timezone.utc)
    booking_id = uuid.uuid4().hex
    first_uid = waiting[0].uid
    first_user = db.query(User).filter(User.uid == first_uid).first()

    booking = Booking(
        booking_id=booking_id,
        tenant_id=tenant_id,
        court_id=court_id,
        sport=sport,
        date=date,
        start_time=start_time,
        end_time=end_time,
        price=price,
        status="confirmed",
        created_by=first_uid,
        created_by_name=first_user.display_name if first_user else None,
        team_id=team_id,
        is_joinable=False,
        slots_total=len(waiting),
        slots_open=0,
        tenant_name=tenant_name,
        created_at=now,
    )
    db.add(booking)

    for mr in waiting:
        wallet = db.query(Wallet).filter(Wallet.uid == mr.uid).with_for_update().first()
        new_balance = wallet.balance - share
        wallet.balance = new_balance
        db.add(WalletTransaction(
            tx_id=uuid.uuid4().hex,
            uid=mr.uid,
            type="debit",
            amount=share,
            currency=wallet.currency,
            reason="Matched into a Join Match game",
            related_booking_id=booking_id,
            balance_after=new_balance,
            created_at=now,
        ))
        db.add(BookingParticipant(booking_id=booking_id, uid=mr.uid, joined_at=now))
        mr.status = "matched"
        mr.matched_booking_id = booking_id

    return booking_id


def create_match_request(db: Session, tenant_id: str, uid: str, req: MatchRequestCreate) -> MatchRequestResponse:
    court = get_court(db, tenant_id, req.court_id)
    if not court.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Court is not active")

    start_min, end_min = to_minutes(req.start_time), to_minutes(req.end_time)
    if end_min <= start_min:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="end_time must be after start_time")
    if start_min < to_minutes(court.open_time) or end_min > to_minutes(court.close_time):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Requested time is outside court operating hours")
    if slot_overlaps_existing(db, tenant_id, req.court_id, req.date, req.start_time, req.end_time):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This slot is already booked")

    waiting_now = _waiting_requests_for_slot(db, tenant_id, req.court_id, req.date, req.start_time, req.end_time)
    if any(mr.uid == uid for mr in waiting_now):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You're already queued for this slot")

    min_players = court.min_players or _min_players_for(court.sport)
    mr = MatchRequest(
        request_id=uuid.uuid4().hex,
        tenant_id=tenant_id,
        court_id=req.court_id,
        sport=court.sport,
        date=req.date,
        start_time=req.start_time,
        end_time=req.end_time,
        uid=uid,
        status="waiting",
        min_players=min_players,
        matched_booking_id=None,
        created_at=datetime.now(timezone.utc),
    )
    db.add(mr)
    db.flush()

    waiting = _waiting_requests_for_slot(db, tenant_id, req.court_id, req.date, req.start_time, req.end_time)
    count_for_response = len(waiting)

    if len(waiting) >= min_players:
        duration_hours = (end_min - start_min) / 60
        price = round(court.hourly_price * duration_hours, 2)

        from app.services.team_service import create_team, add_team_member
        first_uid = waiting[0].uid
        team = create_team(db, first_uid, court.sport, f"{court.sport.title()} Queue Match")
        for w in waiting[1:]:
            try:
                add_team_member(db, team.team_id, w.uid)
            except HTTPException:
                pass

        from app.services.venue_service import get_venue
        venue = get_venue(db, tenant_id)

        formed_booking_id = _form_match(
            db, waiting, tenant_id, req.court_id, court.sport,
            req.date, req.start_time, req.end_time, price, team.team_id,
            tenant_name=venue.name,
        )
        if formed_booking_id:
            try:
                notification_service.notify_match_formed(
                    db, formed_booking_id,
                    [w.uid for w in waiting],
                    venue.name, court.sport,
                    f"{req.start_time}–{req.end_time}",
                )
            except Exception:
                pass

    db.commit()
    db.refresh(mr)
    return _to_response(mr, count_for_response)


def list_match_requests(db: Session, tenant_id: str, court_id: str, date: str) -> list[MatchRequestResponse]:
    mrs = (
        db.query(MatchRequest)
        .filter(
            MatchRequest.tenant_id == tenant_id,
            MatchRequest.court_id == court_id,
            MatchRequest.date == date,
        )
        .all()
    )
    waiting_counts: dict[tuple[str, str], int] = {}
    for mr in mrs:
        if mr.status == "waiting":
            key = (mr.start_time, mr.end_time)
            waiting_counts[key] = waiting_counts.get(key, 0) + 1

    results = []
    for mr in mrs:
        key = (mr.start_time, mr.end_time)
        current = waiting_counts.get(key, 0) if mr.status == "waiting" else mr.min_players
        results.append(_to_response(mr, current))
    return results


def list_my_match_requests(db: Session, uid: str) -> list[MatchRequestResponse]:
    from app.services.venue_service import get_venue

    mrs = (
        db.query(MatchRequest)
        .filter(MatchRequest.uid == uid)
        .order_by(MatchRequest.created_at.desc())
        .all()
    )
    results = []
    for mr in mrs:
        if mr.status == "waiting":
            current = len(
                _waiting_requests_for_slot(db, mr.tenant_id, mr.court_id, mr.date, mr.start_time, mr.end_time)
            )
        else:
            current = mr.min_players
        venue = get_venue(db, mr.tenant_id)
        court = get_court(db, mr.tenant_id, mr.court_id)
        results.append(_to_response(mr, current, tenant_name=venue.name, court_name=court.name))
    return results


def cancel_match_request(db: Session, tenant_id: str, request_id: str, uid: str) -> MatchRequestResponse:
    mr = (
        db.query(MatchRequest)
        .filter(MatchRequest.request_id == request_id, MatchRequest.tenant_id == tenant_id)
        .first()
    )
    if not mr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match request not found")
    if mr.uid != uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your match request")
    if mr.status != "waiting":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Request already {mr.status}")
    mr.status = "cancelled"
    db.commit()
    return _to_response(mr, 0)
