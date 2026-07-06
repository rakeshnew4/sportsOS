from fastapi import APIRouter, Depends

from app.core.db import Client, get_db
from app.core.security import CurrentUser, get_current_user
from app.models.venue import VenueCreateRequest, VenueResponse
from app.services import venue_service

router = APIRouter(prefix="/venues", tags=["venues"])


@router.post("", status_code=201)
def create_venue(
    req: VenueCreateRequest,
    user: CurrentUser = Depends(get_current_user),
    db: Client = Depends(get_db),
) -> VenueResponse:
    return venue_service.create_venue(db, user.uid, req)


@router.get("/{tenant_id}")
def get_venue(
    tenant_id: str,
    db: Client = Depends(get_db),
) -> VenueResponse:
    return venue_service.get_venue(db, tenant_id)
