from fastapi import APIRouter, Depends

from app.core.db import Client, get_db
from app.core.security import CurrentUser, get_current_user
from app.models.booking import BookingResponse
from app.models.match import MatchResponse, OpenToCommunityRequest, ParticipantResponse
from app.services import match_service

router = APIRouter(tags=["matches"])


@router.patch("/venues/{tenant_id}/bookings/{booking_id}/open-to-community")
def open_to_community(
    tenant_id: str,
    booking_id: str,
    req: OpenToCommunityRequest,
    user: CurrentUser = Depends(get_current_user),
    db: Client = Depends(get_db),
) -> BookingResponse:
    return match_service.open_to_community(db, tenant_id, booking_id, user.uid, req)


@router.get("/matches")
def discover_matches(
    sport: str | None = None,
    date: str | None = None,
    db: Client = Depends(get_db),
) -> list[MatchResponse]:
    return match_service.discover_matches(db, sport, date)


@router.post("/venues/{tenant_id}/bookings/{booking_id}/join")
def join_match(
    tenant_id: str,
    booking_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Client = Depends(get_db),
) -> BookingResponse:
    return match_service.join_match(db, tenant_id, booking_id, user.uid)


@router.get("/venues/{tenant_id}/bookings/{booking_id}/participants")
def list_participants(
    tenant_id: str,
    booking_id: str,
    db: Client = Depends(get_db),
) -> list[ParticipantResponse]:
    return match_service.list_participants(db, tenant_id, booking_id)
