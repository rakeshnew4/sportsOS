from typing import Literal

from pydantic import BaseModel

BookingStatus = Literal["pending_payment", "confirmed", "completed", "cancelled"]


class BookingCreateRequest(BaseModel):
    court_id: str
    date: str  # "YYYY-MM-DD"
    start_time: str  # "HH:MM"
    end_time: str  # "HH:MM"
    team_name: str | None = None  # Optional team name; auto-generated if not provided


class BookingRescheduleRequest(BaseModel):
    date: str  # "YYYY-MM-DD"
    start_time: str  # "HH:MM"
    end_time: str  # "HH:MM"
    court_id: str | None = None  # Move to a different court on the same venue; same court if omitted


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
    created_by_name: str | None = None
    team_id: str | None = None
    team_name: str | None = None
    is_joinable: bool
    slots_total: int
    slots_open: int
    tenant_name: str | None = None
    court_name: str | None = None


class TimeRange(BaseModel):
    start_time: str
    end_time: str


class AvailabilityResponse(BaseModel):
    court_id: str
    date: str
    open_slots: list[TimeRange]
    booked_slots: list[TimeRange]


class SlotResponse(BaseModel):
    start_time: str
    end_time: str
    available: bool
    price: float | None = None
