from typing import Literal

from pydantic import BaseModel

MatchRequestStatus = Literal["waiting", "matched", "cancelled"]


class MatchRequestCreate(BaseModel):
    court_id: str
    date: str  # "YYYY-MM-DD"
    start_time: str  # "HH:MM"
    end_time: str  # "HH:MM"


class MatchRequestResponse(BaseModel):
    request_id: str
    tenant_id: str
    court_id: str
    sport: str
    date: str
    start_time: str
    end_time: str
    uid: str
    status: MatchRequestStatus
    min_players: int
    current_count: int
    matched_booking_id: str | None = None
