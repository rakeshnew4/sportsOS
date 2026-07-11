from pydantic import BaseModel


class GeoPoint(BaseModel):
    lat: float
    lng: float


class VenueCreateRequest(BaseModel):
    name: str
    city: str
    geo: GeoPoint
    sports: list[str]
    description: str | None = None
    address: str | None = None
    amenities: list[str] = []
    cover_image_url: str | None = None
    upi_id: str | None = None
    booking_phone: str | None = None


class VenueUpdateRequest(BaseModel):
    name: str | None = None
    city: str | None = None
    description: str | None = None
    address: str | None = None
    amenities: list[str] | None = None
    cover_image_url: str | None = None
    upi_id: str | None = None
    booking_phone: str | None = None


class VenueResponse(BaseModel):
    tenant_id: str
    name: str
    city: str
    geo: GeoPoint
    sports: list[str]
    description: str | None = None
    address: str | None = None
    amenities: list[str] = []
    cover_image_url: str | None = None
    upi_id: str | None = None
    booking_phone: str | None = None
