from fastapi import APIRouter, Depends

from app.core.db import Session, get_db
from app.core.security import CurrentUser, get_current_user
from app.models.user import LoginRequest, MeResponse, OwnerRegisterRequest, PlayerRegisterRequest
from app.services import user_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register/player", status_code=201)
def register_player(
    req: PlayerRegisterRequest,
    db: Session = Depends(get_db),
) -> MeResponse:
    return user_service.register_player(db, req)


@router.post("/register/owner", status_code=201)
def register_owner(
    req: OwnerRegisterRequest,
    db: Session = Depends(get_db),
) -> MeResponse:
    return user_service.register_owner(db, req)


@router.post("/login")
def login(
    req: LoginRequest,
    db: Session = Depends(get_db),
) -> MeResponse:
    return user_service.login(db, req.phone)


@router.get("/me")
def get_me(
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MeResponse:
    return user_service.get_me(db, user.uid)
