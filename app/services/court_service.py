import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.orm import Court
from app.models.court import CourtCreateRequest, CourtResponse, CourtUpdateRequest


def create_court(db: Session, tenant_id: str, req: CourtCreateRequest) -> CourtResponse:
    if req.min_players is not None and req.min_players < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="min_players must be at least 1")
    court = Court(
        court_id=uuid.uuid4().hex,
        tenant_id=tenant_id,
        name=req.name,
        sport=req.sport,
        hourly_price=req.hourly_price,
        open_time=req.open_time,
        close_time=req.close_time,
        is_active=True,
        dynamic_pricing_enabled=req.dynamic_pricing_enabled,
        min_players=req.min_players,
    )
    db.add(court)
    db.commit()
    db.refresh(court)
    return _to_response(court)


def list_courts(db: Session, tenant_id: str) -> list[CourtResponse]:
    courts = db.query(Court).filter(Court.tenant_id == tenant_id).all()
    return [_to_response(c) for c in courts]


def get_court(db: Session, tenant_id: str, court_id: str) -> CourtResponse:
    court = (
        db.query(Court)
        .filter(Court.court_id == court_id, Court.tenant_id == tenant_id)
        .first()
    )
    if not court:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Court not found")
    return _to_response(court)


def update_court(db: Session, tenant_id: str, court_id: str, req: CourtUpdateRequest) -> CourtResponse:
    court = (
        db.query(Court)
        .filter(Court.court_id == court_id, Court.tenant_id == tenant_id)
        .first()
    )
    if not court:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Court not found")
    if req.min_players is not None and req.min_players < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="min_players must be at least 1")
    updates = {k: v for k, v in req.model_dump(exclude_unset=True).items() if v is not None}
    for key, value in updates.items():
        setattr(court, key, value)
    db.commit()
    db.refresh(court)
    return _to_response(court)


def _to_response(c: Court) -> CourtResponse:
    return CourtResponse(
        court_id=c.court_id,
        tenant_id=c.tenant_id,
        name=c.name,
        sport=c.sport,
        hourly_price=c.hourly_price,
        open_time=c.open_time,
        close_time=c.close_time,
        is_active=c.is_active,
        dynamic_pricing_enabled=c.dynamic_pricing_enabled,
        min_players=c.min_players,
    )
