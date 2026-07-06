from fastapi import APIRouter, Depends

from app.core.db import Client, get_db
from app.core.security import CurrentUser, get_current_user
from app.models.user import MeResponse, OwnerRegisterRequest, PlayerRegisterRequest
from app.services import user_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register/player", status_code=201)
def register_player(
    req: PlayerRegisterRequest,
    user: CurrentUser = Depends(get_current_user),
    db: Client = Depends(get_db),
) -> MeResponse:
    user_service.register_player(db, user.uid, req)
    return user_service.get_me(db, user.uid)


@router.post("/register/owner", status_code=201)
def register_owner(
    req: OwnerRegisterRequest,
    user: CurrentUser = Depends(get_current_user),
    db: Client = Depends(get_db),
) -> MeResponse:
    user_service.register_owner(db, user.uid, req)
    return user_service.get_me(db, user.uid)


@router.get("/me")
def get_me(
    user: CurrentUser = Depends(get_current_user),
    db: Client = Depends(get_db),
) -> MeResponse:
    return user_service.get_me(db, user.uid)
