from fastapi import APIRouter, Depends

from app.core.db import Session, get_db
from app.core.security import CurrentUser, get_current_user
from app.models.user import AdminLoginRequest, LoginRequest, MeResponse, PlayerRegisterRequest
from app.services import user_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register/player", status_code=201)
def register_player(
    req: PlayerRegisterRequest,
    db: Session = Depends(get_db),
) -> MeResponse:
    return user_service.register_player(db, req)


# There is intentionally no public "/register/owner" — venue owner/admin accounts
# are provisioned by a superadmin (see app/routers/admin_accounts.py) and log in
# with a password via /auth/admin/login, not self-serve phone signup.


@router.post("/login")
def login(
    req: LoginRequest,
    db: Session = Depends(get_db),
) -> MeResponse:
    return user_service.login(db, req.phone)


@router.post("/admin/login")
def admin_login(
    req: AdminLoginRequest,
    db: Session = Depends(get_db),
) -> MeResponse:
    return user_service.admin_login(db, req.email, req.password)


@router.get("/me")
def get_me(
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MeResponse:
    return user_service.get_me(db, user.uid)
