"""Venue staff management."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.db import Session, get_db
from app.core.security import CurrentUser, get_current_user, require_venue_access
from app.db.orm import User, UserRole
from app.services.user_service import grant_owner_role, grant_staff_role

router = APIRouter(prefix="/venues/{tenant_id}/staff", tags=["venue-staff"])


class StaffMember(BaseModel):
    uid: str
    display_name: str | None = None
    role: str
    added_at: str


class AddStaffRequest(BaseModel):
    user_uid: str
    role: str = "staff"


@router.get("")
def list_staff(
    tenant_id: str,
    user: CurrentUser = Depends(require_venue_access),
    db: Session = Depends(get_db),
) -> list[StaffMember]:
    roles = db.query(UserRole).filter(UserRole.tenant_id == tenant_id).all()
    results = []
    for r in roles:
        u = db.query(User).filter(User.uid == r.uid).first()
        results.append(StaffMember(
            uid=r.uid, display_name=u.display_name if u else None,
            role=r.role_type, added_at="",
        ))
    return results


@router.post("", status_code=201)
def add_staff(
    tenant_id: str,
    req: AddStaffRequest,
    user: CurrentUser = Depends(require_venue_access),
    db: Session = Depends(get_db),
) -> StaffMember:
    if tenant_id not in user.owner_of:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only venue owners can add staff")
    target = db.query(User).filter(User.uid == req.user_uid).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if req.role == "owner":
        grant_owner_role(db, req.user_uid, tenant_id)
    else:
        grant_staff_role(db, req.user_uid, tenant_id)
    db.commit()
    return StaffMember(uid=req.user_uid, display_name=target.display_name, role=req.role, added_at="")


@router.delete("/{staff_uid}")
def remove_staff(
    tenant_id: str,
    staff_uid: str,
    user: CurrentUser = Depends(require_venue_access),
    db: Session = Depends(get_db),
) -> dict:
    if tenant_id not in user.owner_of:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only venue owners can remove staff")
    roles = db.query(UserRole).filter(UserRole.uid == staff_uid, UserRole.tenant_id == tenant_id).all()
    for r in roles:
        db.delete(r)
    db.commit()
    return {"success": True, "message": f"Staff member {staff_uid} removed"}



