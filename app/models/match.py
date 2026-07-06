from pydantic import BaseModel

from app.models.booking import BookingResponse
from app.models.venue import GeoPoint


class OpenToCommunityRequest(BaseModel):
    slots_open: int


class MatchResponse(BookingResponse):
    tenant_name: str
    geo: GeoPoint


class ParticipantResponse(BaseModel):
    uid: str
    display_name: str | None = None
    joined_at: str
