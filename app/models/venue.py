from pydantic import BaseModel


class GeoPoint(BaseModel):
    lat: float
    lng: float


class VenueCreateRequest(BaseModel):
    name: str
    city: str
    geo: GeoPoint
    sports: list[str]


class VenueResponse(BaseModel):
    tenant_id: str
    name: str
    city: str
    geo: GeoPoint
    sports: list[str]
