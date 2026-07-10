"""Cross-venue match invite inbox — responding to invites regardless of which booking/venue they came from."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.db import Session, get_db
from app.core.security import CurrentUser, get_current_user
from app.services import invite_service

router = APIRouter(prefix="/invites", tags=["invites"])


class MatchInviteResponse(BaseModel):
    invite_id: str
    booking_id: str
    from_uid: str
    to_uid: str
    tier: str
    status: str
    title: str
    body: str
    created_at: str


class RespondRequest(BaseModel):
    accept: bool


@router.get("/me")
def get_my_invites(
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MatchInviteResponse]:
    """Pending match invites for the current player."""
    invites = invite_service.get_my_pending_invites(db, user.uid)
    return [
        MatchInviteResponse(
            invite_id=i.invite_id, booking_id=i.booking_id, from_uid=i.from_uid, to_uid=i.to_uid,
            tier=i.tier, status=i.status, title=i.title, body=i.body, created_at=i.created_at.isoformat(),
        )
        for i in invites
    ]


@router.post("/{invite_id}/respond")
def respond_to_invite(
    invite_id: str,
    req: RespondRequest,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Accept or decline a match invite. Accepting joins the booking's participant list and team."""
    return invite_service.respond_to_invite(db, invite_id, user.uid, req.accept)
