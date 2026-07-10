from typing import Literal

from pydantic import BaseModel

TeamStatus = Literal["forming", "active", "completed", "cancelled"]


class TeamMember(BaseModel):
    uid: str
    display_name: str | None = None
    joined_at: str


class TeamCreateRequest(BaseModel):
    team_name: str
    sport: str


class TeamMatchHistory(BaseModel):
    """Team match history record."""
    match_id: str
    booking_id: str
    opponent_team_id: str
    opponent_team_name: str
    result: Literal["win", "loss", "draw"]
    player_count: int
    played_at: str
    venue_id: str | None = None


class TeamStats(BaseModel):
    """Team statistics."""
    total_matches: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    win_rate: float = 0.0
    rating: float = 1200.0  # ELO starting rating
    last_match_at: str | None = None


class TeamResponse(BaseModel):
    team_id: str
    team_name: str
    sport: str
    captain_uid: str
    captain_name: str | None = None
    status: TeamStatus
    members: list[TeamMember]
    total_members: int
    stats: TeamStats | None = None
    created_at: str
    created_by: str | None = None
    booking_id: str | None = None
