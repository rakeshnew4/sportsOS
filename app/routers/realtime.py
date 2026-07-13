"""Mints Firebase custom tokens so clients can sign in to Firebase Auth with
their existing session uid and get read-only Firestore access for live
Join Match / slot-availability state. Firestore security rules deny all
client writes — every mutation still goes through the regular REST API.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import CurrentUser, get_current_user
from app.services import realtime_service

router = APIRouter(prefix="/realtime", tags=["realtime"])


@router.post("/token")
def get_realtime_token(user: CurrentUser = Depends(get_current_user)) -> dict:
    token = realtime_service.mint_custom_token(user.uid)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Realtime features are not configured on this server",
        )
    return {"token": token}
