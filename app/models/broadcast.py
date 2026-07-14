from typing import Literal

from pydantic import BaseModel

BroadcastTarget = Literal["all_players", "all_admins", "sport", "court", "team"]


class BroadcastRequest(BaseModel):
    target: BroadcastTarget
    title: str
    body: str
    # Required depending on target (validated in broadcast_service):
    # sport -> sport, court -> court_id, team -> team_id.
    sport: str | None = None
    court_id: str | None = None
    team_id: str | None = None
    # Optional narrowing filters, usable with all_players / all_admins / sport.
    tenant_id: str | None = None
    city: str | None = None


class BroadcastResponse(BaseModel):
    recipient_count: int
