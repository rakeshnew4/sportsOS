from typing import Literal

from pydantic import BaseModel

BookingStatus = Literal["pending_payment", "confirmed", "completed", "cancelled"]


class BookingCreateRequest(BaseModel):
    court_id: str
    date: str  # "YYYY-MM-DD"
    start_time: str  # "HH:MM"
    end_time: str  # "HH:MM"
    team_name: str | None = None  # Optional team name; auto-generated if not provided


class BookingResponse(BaseModel):
    booking_id: str
    tenant_id: str
    court_id: str
    sport: str
    date: str
    start_time: str
    end_time: str
    price: float
    status: BookingStatus
    created_by: str
    team_id: str | None = None
    team_name: str | None = None
    is_joinable: bool
    slots_total: int
    slots_open: int


class TimeRange(BaseModel):
    start_time: str
    end_time: str


class AvailabilityResponse(BaseModel):
    court_id: str
    date: str
    open_slots: list[TimeRange]
    booked_slots: list[TimeRange]
