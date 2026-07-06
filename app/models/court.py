from pydantic import BaseModel


class CourtCreateRequest(BaseModel):
    name: str
    sport: str
    hourly_price: float
    open_time: str  # "06:00"
    close_time: str  # "23:00"


class CourtUpdateRequest(BaseModel):
    name: str | None = None
    hourly_price: float | None = None
    open_time: str | None = None
    close_time: str | None = None
    is_active: bool | None = None


class CourtResponse(BaseModel):
    court_id: str
    tenant_id: str
    name: str
    sport: str
    hourly_price: float
    open_time: str
    close_time: str
    is_active: bool
