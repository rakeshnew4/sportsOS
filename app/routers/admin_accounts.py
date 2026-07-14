"""Superadmin-only management of venue owner/admin login accounts.

There is no public self-signup for these — a superadmin creates them here
and hands the resulting email/password to the venue owner out of band.
"""

from fastapi import APIRouter, Depends

from app.core.db import Session, get_db
from app.core.security import require_superadmin
from app.models.user import AdminAccountCreateRequest, AdminAccountResponse, AdminPasswordResetResponse, MeResponse
from app.services import user_service

router = APIRouter(prefix="/admin/accounts", tags=["admin-accounts"], dependencies=[Depends(require_superadmin)])


@router.get("")
def list_accounts(db: Session = Depends(get_db)) -> list[AdminAccountResponse]:
    return user_service.list_admin_accounts(db)


@router.post("", status_code=201)
def create_account(
    req: AdminAccountCreateRequest,
    db: Session = Depends(get_db),
) -> MeResponse:
    return user_service.create_admin_account(db, req)


@router.post("/{uid}/reset-password")
def reset_password(uid: str, db: Session = Depends(get_db)) -> AdminPasswordResetResponse:
    return user_service.reset_admin_password(db, uid)
