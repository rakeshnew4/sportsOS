import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.orm import Tenant
from app.models.venue import GeoPoint, VenueCreateRequest, VenueResponse
from app.services.user_service import grant_owner_role


def create_venue(db: Session, uid: str, req: VenueCreateRequest) -> VenueResponse:
    tenant_id = uuid.uuid4().hex
    tenant = Tenant(
        tenant_id=tenant_id,
        name=req.name,
        city=req.city,
        geo_lat=req.geo.lat,
        geo_lng=req.geo.lng,
        sports=req.sports,
        created_at=datetime.now(timezone.utc),
    )
    db.add(tenant)
    grant_owner_role(db, uid, tenant_id)
    db.commit()
    return VenueResponse(
        tenant_id=tenant_id,
        name=req.name,
        city=req.city,
        geo=req.geo,
        sports=req.sports,
    )


def list_venues(db: Session, city: str | None = None, sport: str | None = None) -> list[VenueResponse]:
    query = db.query(Tenant)
    if city:
        query = query.filter(Tenant.city.ilike(city))
    tenants = query.all()
    results = []
    for t in tenants:
        if sport and sport not in (t.sports or []):
            continue
        results.append(_to_response(t))
    return results


def get_venue(db: Session, tenant_id: str) -> VenueResponse:
    tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venue not found")
    return _to_response(tenant)


def _to_response(t: Tenant) -> VenueResponse:
    return VenueResponse(
        tenant_id=t.tenant_id,
        name=t.name,
        city=t.city,
        geo=GeoPoint(lat=t.geo_lat, lng=t.geo_lng),
        sports=t.sports or [],
    )
