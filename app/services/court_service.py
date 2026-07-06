from fastapi import HTTPException, status

from app.core.db import Client
from app.models.court import CourtCreateRequest, CourtResponse, CourtUpdateRequest


def _courts_ref(db: Client, tenant_id: str):
    return db.collection("tenants").document(tenant_id).collection("courts")


def create_court(db: Client, tenant_id: str, req: CourtCreateRequest) -> CourtResponse:
    court_ref = _courts_ref(db, tenant_id).document()
    data = {
        "name": req.name,
        "sport": req.sport,
        "hourly_price": req.hourly_price,
        "open_time": req.open_time,
        "close_time": req.close_time,
        "is_active": True,
    }
    court_ref.set(data)
    return CourtResponse(court_id=court_ref.id, tenant_id=tenant_id, **data)


def list_courts(db: Client, tenant_id: str) -> list[CourtResponse]:
    docs = _courts_ref(db, tenant_id).stream()
    return [CourtResponse(court_id=doc.id, tenant_id=tenant_id, **doc.to_dict()) for doc in docs]


def get_court(db: Client, tenant_id: str, court_id: str) -> CourtResponse:
    doc = _courts_ref(db, tenant_id).document(court_id).get()
    if not doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Court not found")
    return CourtResponse(court_id=court_id, tenant_id=tenant_id, **doc.to_dict())


def update_court(db: Client, tenant_id: str, court_id: str, req: CourtUpdateRequest) -> CourtResponse:
    court_ref = _courts_ref(db, tenant_id).document(court_id)
    if not court_ref.get().exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Court not found")
    updates = {k: v for k, v in req.model_dump(exclude_unset=True).items() if v is not None}
    if updates:
        court_ref.update(updates)
    return get_court(db, tenant_id, court_id)
