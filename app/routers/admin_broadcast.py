"""Superadmin broadcast notifications — send to all players, all admins,
everyone tied to a sport/court/team, with optional venue/city narrowing.
"""

from fastapi import APIRouter, Depends

from app.core.db import Session, get_db
from app.core.security import require_superadmin
from app.models.broadcast import BroadcastRequest, BroadcastResponse
from app.services import broadcast_service

router = APIRouter(prefix="/admin/broadcast", tags=["admin-broadcast"], dependencies=[Depends(require_superadmin)])


@router.post("")
def send_broadcast(req: BroadcastRequest, db: Session = Depends(get_db)) -> BroadcastResponse:
    count = broadcast_service.send_broadcast(db, req)
    return BroadcastResponse(recipient_count=count)
