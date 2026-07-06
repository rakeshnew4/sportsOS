from fastapi import APIRouter, Depends

from app.core.db import Client, get_db
from app.core.security import CurrentUser, get_current_user, require_venue_access
from app.models.booking import AvailabilityResponse, BookingCreateRequest, BookingResponse
from app.services import booking_service

router = APIRouter(tags=["bookings"])


@router.get("/venues/{tenant_id}/courts/{court_id}/availability")
def get_availability(
    tenant_id: str,
    court_id: str,
    date: str,
    db: Client = Depends(get_db),
) -> AvailabilityResponse:
    return booking_service.get_availability(db, tenant_id, court_id, date)


@router.post("/venues/{tenant_id}/bookings", status_code=201)
def create_booking(
    tenant_id: str,
    req: BookingCreateRequest,
    user: CurrentUser = Depends(get_current_user),
    db: Client = Depends(get_db),
) -> BookingResponse:
    return booking_service.create_booking(db, tenant_id, user.uid, req)


@router.get("/venues/{tenant_id}/bookings")
def list_venue_bookings(
    tenant_id: str,
    date: str | None = None,
    user: CurrentUser = Depends(require_venue_access),
    db: Client = Depends(get_db),
) -> list[BookingResponse]:
    return booking_service.list_venue_bookings(db, tenant_id, date)


@router.get("/players/me/bookings")
def list_my_bookings(
    user: CurrentUser = Depends(get_current_user),
    db: Client = Depends(get_db),
) -> list[BookingResponse]:
    return booking_service.list_my_bookings(db, user.uid)


@router.patch("/venues/{tenant_id}/bookings/{booking_id}/cancel")
def cancel_booking(
    tenant_id: str,
    booking_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Client = Depends(get_db),
) -> BookingResponse:
    return booking_service.cancel_booking(db, tenant_id, booking_id, user.uid, user.can_manage(tenant_id))
