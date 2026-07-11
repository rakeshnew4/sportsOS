from pydantic import BaseModel


class CourtCreateRequest(BaseModel):
    name: str
    sport: str
    hourly_price: float
    open_time: str  # "06:00"
    close_time: str  # "23:00"
    dynamic_pricing_enabled: bool = False
    min_players: int | None = None  # Players needed in the "Join Match" queue to auto-confirm a booking; None = sport default


class CourtUpdateRequest(BaseModel):
    name: str | None = None
    hourly_price: float | None = None
    open_time: str | None = None
    close_time: str | None = None
    is_active: bool | None = None
    min_players: int | None = None


class CourtResponse(BaseModel):
    court_id: str
    tenant_id: str
    name: str
    sport: str
    hourly_price: float
    open_time: str
    close_time: str
    is_active: bool
    dynamic_pricing_enabled: bool = False
    min_players: int | None = None
