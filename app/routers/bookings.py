from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.db import Session, get_db
from app.core.security import CurrentUser, get_current_user, require_venue_access
from app.models.booking import AvailabilityResponse, BookingCreateRequest, BookingResponse, SlotResponse
from app.services import booking_service, invite_service

router = APIRouter(tags=["bookings"])


class CheckinRequest(BaseModel):
    """Mark a player as checked in to a match."""
    player_uid: str


class InviteCandidate(BaseModel):
    uid: str
    display_name: str
    tier: str
    reason: str


class InviteItem(BaseModel):
    to_uid: str
    tier: str


class SendInvitesRequest(BaseModel):
    invites: list[InviteItem]


class MatchInviteResponse(BaseModel):
    invite_id: str
    booking_id: str
    from_uid: str
    to_uid: str
    tier: str
    status: str
    title: str
    body: str
    created_at: str


class MatchCompletionResponse(BaseModel):
    """Response when match is marked complete."""
    booking_id: str
    status: str
    completed_at: str
    players_checked_in: int
    total_players: int
    captain_rewards_earned: float
    message: str


@router.get("/venues/{tenant_id}/courts/{court_id}/availability")
def get_availability(
    tenant_id: str,
    court_id: str,
    date: str,
    db: Session = Depends(get_db),
) -> AvailabilityResponse:
    return booking_service.get_availability(db, tenant_id, court_id, date)


@router.get("/venues/{tenant_id}/courts/{court_id}/slots")
def get_slots(
    tenant_id: str,
    court_id: str,
    date: str,
    granularity: int = 30,
    db: Session = Depends(get_db),
) -> list[SlotResponse]:
    return booking_service.get_slots(db, tenant_id, court_id, date, granularity)


@router.post("/venues/{tenant_id}/bookings", status_code=201)
def create_booking(
    tenant_id: str,
    req: BookingCreateRequest,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BookingResponse:
    return booking_service.create_booking(db, tenant_id, user.uid, req)


@router.get("/venues/{tenant_id}/bookings")
def list_venue_bookings(
    tenant_id: str,
    date: str | None = None,
    user: CurrentUser = Depends(require_venue_access),
    db: Session = Depends(get_db),
) -> list[BookingResponse]:
    return booking_service.list_venue_bookings(db, tenant_id, date)


@router.get("/players/me/bookings")
def list_my_bookings(
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[BookingResponse]:
    return booking_service.list_my_bookings(db, user.uid)


@router.patch("/venues/{tenant_id}/bookings/{booking_id}/cancel")
def cancel_booking(
    tenant_id: str,
    booking_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BookingResponse:
    return booking_service.cancel_booking(db, tenant_id, booking_id, user.uid, user.can_manage(tenant_id))


@router.post("/venues/{tenant_id}/bookings/{booking_id}/checkin")
def checkin_player(
    tenant_id: str,
    booking_id: str,
    req: CheckinRequest,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Check in a player to a match (QR code scan or manual)."""
    return booking_service.checkin_player(db, tenant_id, booking_id, req.player_uid, user.uid)


@router.post("/venues/{tenant_id}/bookings/{booking_id}/complete")
def complete_match(
    tenant_id: str,
    booking_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MatchCompletionResponse:
    """Mark match as completed (after QR check-ins are done). Triggers reward issuance."""
    return booking_service.complete_match(db, tenant_id, booking_id, user.uid)


@router.get("/venues/{tenant_id}/bookings/{booking_id}/checkins")
def get_checkins(
    tenant_id: str,
    booking_id: str,
    db: Session = Depends(get_db),
) -> dict:
    """Get check-in status for all players in a match."""
    return booking_service.get_checkins(db, tenant_id, booking_id)


@router.get("/venues/{tenant_id}/bookings/{booking_id}/invite-candidates")
def get_invite_candidates(
    tenant_id: str,
    booking_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[InviteCandidate]:
    """Ranked, tiered list of players the captain can invite: playmates first, then queued players, then opted-in nearby players."""
    candidates = invite_service.get_invite_candidates(db, tenant_id, booking_id, user.uid)
    return [InviteCandidate(**c) for c in candidates]


@router.post("/venues/{tenant_id}/bookings/{booking_id}/invites", status_code=201)
def send_invites(
    tenant_id: str,
    booking_id: str,
    req: SendInvitesRequest,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MatchInviteResponse]:
    """Send match invites (AI-personalized notification text where available)."""
    invites = invite_service.send_invites(
        db, tenant_id, booking_id, user.uid, [i.model_dump() for i in req.invites]
    )
    return [
        MatchInviteResponse(
            invite_id=i.invite_id, booking_id=i.booking_id, from_uid=i.from_uid, to_uid=i.to_uid,
            tier=i.tier, status=i.status, title=i.title, body=i.body, created_at=i.created_at.isoformat(),
        )
        for i in invites
    ]
