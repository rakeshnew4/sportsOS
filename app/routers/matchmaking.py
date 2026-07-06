from fastapi import APIRouter, Depends

from app.core.db import Client, get_db
from app.core.security import CurrentUser, get_current_user
from app.models.matchmaking import MatchRequestCreate, MatchRequestResponse
from app.services import matchmaking_service

router = APIRouter(prefix="/venues/{tenant_id}/match-requests", tags=["matchmaking"])


@router.post("", status_code=201)
def create_match_request(
    tenant_id: str,
    req: MatchRequestCreate,
    user: CurrentUser = Depends(get_current_user),
    db: Client = Depends(get_db),
) -> MatchRequestResponse:
    return matchmaking_service.create_match_request(db, tenant_id, user.uid, req)


@router.get("")
def list_match_requests(
    tenant_id: str,
    court_id: str,
    date: str,
    db: Client = Depends(get_db),
) -> list[MatchRequestResponse]:
    return matchmaking_service.list_match_requests(db, tenant_id, court_id, date)


@router.delete("/{request_id}")
def cancel_match_request(
    tenant_id: str,
    request_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Client = Depends(get_db),
) -> MatchRequestResponse:
    return matchmaking_service.cancel_match_request(db, tenant_id, request_id, user.uid)
