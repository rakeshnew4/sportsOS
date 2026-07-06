from datetime import UTC, datetime

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
    if start_min < to_minutes(court.open_time) or end_min > to_minutes(court.close_time):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Requested time is outside court operating hours"
        )

    if slot_overlaps_existing(db, tenant_id, req.court_id, req.date, req.start_time, req.end_time):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slot overlaps an existing booking")

    duration_hours = (end_min - start_min) / 60
    price = round(court.hourly_price * duration_hours, 2)

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
        "is_joinable": False,
        "slots_total": 0,
        "slots_open": 0,
        "tenant_name": None,
        "geo": None,
        "created_at": datetime.now(UTC).isoformat(),
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
    return booking_to_response(tenant_id, booking_id, data)
