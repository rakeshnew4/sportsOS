from fastapi import APIRouter, Depends

from app.core.db import Session, get_db
from app.core.security import CurrentUser, require_venue_access
from app.models.court import CourtCreateRequest, CourtResponse, CourtUpdateRequest
from app.services import court_service

router = APIRouter(prefix="/venues/{tenant_id}/courts", tags=["courts"])


@router.post("", status_code=201)
def create_court(
    tenant_id: str,
    req: CourtCreateRequest,
    user: CurrentUser = Depends(require_venue_access),
    db: Session = Depends(get_db),
) -> CourtResponse:
    return court_service.create_court(db, tenant_id, req)


@router.get("")
def list_courts(
    tenant_id: str,
    db: Session = Depends(get_db),
) -> list[CourtResponse]:
    return court_service.list_courts(db, tenant_id)


@router.get("/{court_id}")
def get_court(
    tenant_id: str,
    court_id: str,
    db: Session = Depends(get_db),
) -> CourtResponse:
    return court_service.get_court(db, tenant_id, court_id)


@router.patch("/{court_id}")
def update_court(
    tenant_id: str,
    court_id: str,
    req: CourtUpdateRequest,
    user: CurrentUser = Depends(require_venue_access),
    db: Session = Depends(get_db),
) -> CourtResponse:
    return court_service.update_court(db, tenant_id, court_id, req)
