from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.core.db import Client
from app.models.venue import GeoPoint, VenueCreateRequest, VenueResponse
from app.services.user_service import grant_owner_role


def create_venue(db: Client, uid: str, req: VenueCreateRequest) -> VenueResponse:
    tenant_ref = db.collection("tenants").document()
    tenant_ref.set(
        {
            "name": req.name,
            "city": req.city,
            "geo": req.geo.model_dump(),
            "sports": req.sports,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    grant_owner_role(db, uid, tenant_ref.id)
    return VenueResponse(tenant_id=tenant_ref.id, name=req.name, city=req.city, geo=req.geo, sports=req.sports)


def get_venue(db: Client, tenant_id: str) -> VenueResponse:
    doc = db.collection("tenants").document(tenant_id).get()
    if not doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venue not found")
    data = doc.to_dict()
    return VenueResponse(
        tenant_id=tenant_id,
        name=data["name"],
        city=data["city"],
        geo=GeoPoint(**data["geo"]),
        sports=data["sports"],
    )
