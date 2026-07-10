"""Venue staff management - Phase 1 (B2B feature)."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.db import Client, get_db
from app.core.security import CurrentUser, get_current_user, require_venue_access

router = APIRouter(prefix="/venues/{tenant_id}/staff", tags=["venue-staff"])


class StaffMember(BaseModel):
    """Venue staff member."""
    uid: str
    display_name: str | None = None
    role: str  # "owner" | "staff"
    added_at: str


class AddStaffRequest(BaseModel):
    """Request to add staff to venue."""
    user_uid: str
    role: str = "staff"  # "staff" or "admin"


@router.get("")
def list_staff(
    tenant_id: str,
    user: CurrentUser = Depends(require_venue_access),
    db: Client = Depends(get_db),
) -> list[StaffMember]:
    """List all staff members for a venue."""
    venue_doc = db.collection("tenants").document(tenant_id).get()
    if not venue_doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venue not found")

    staff_members = []
    users_collection = db.collection("users")

    # Get all users and find those with staff_of = [tenant_id]
    for user_doc in users_collection.stream():
        user_data = user_doc.to_dict()
        roles = user_data.get("roles", {})

        if tenant_id in roles.get("owner", []):
            staff_members.append(StaffMember(
                uid=user_doc.id,
                display_name=user_data.get("display_name"),
                role="owner",
                added_at=user_data.get("created_at", "")
            ))
        elif tenant_id in roles.get("staff", []):
            staff_members.append(StaffMember(
                uid=user_doc.id,
                display_name=user_data.get("display_name"),
                role="staff",
                added_at=user_data.get("updated_at", "")
            ))

    return staff_members


@router.post("", status_code=201)
def add_staff(
    tenant_id: str,
    req: AddStaffRequest,
    user: CurrentUser = Depends(require_venue_access),
    db: Client = Depends(get_db),
) -> StaffMember:
    """Add a staff member to a venue (owner only)."""
    # Only owners can add staff (not staff themselves)
    if tenant_id not in user.owner_of:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only venue owners can add staff"
        )

    # Verify user exists
    user_doc = db.collection("users").document(req.user_uid).get()
    if not user_doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user_data = user_doc.to_dict()
    roles = user_data.get("roles", {})

    # Add to appropriate role
    if req.role == "owner":
        owner_list = roles.get("owner", [])
        if tenant_id not in owner_list:
            owner_list.append(tenant_id)
        roles["owner"] = owner_list
    else:
        staff_list = roles.get("staff", [])
        if tenant_id not in staff_list:
            staff_list.append(tenant_id)
        roles["staff"] = staff_list

    db.collection("users").document(req.user_uid).update({"roles": roles})

    return StaffMember(
        uid=req.user_uid,
        display_name=user_data.get("display_name"),
        role=req.role,
        added_at=user_data.get("updated_at", "")
    )


@router.delete("/{staff_uid}")
def remove_staff(
    tenant_id: str,
    staff_uid: str,
    user: CurrentUser = Depends(require_venue_access),
    db: Client = Depends(get_db),
) -> dict:
    """Remove a staff member from a venue (owner only)."""
    # Only owners can remove staff
    if tenant_id not in user.owner_of:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only venue owners can remove staff"
        )

    user_doc = db.collection("users").document(staff_uid).get()
    if not user_doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user_data = user_doc.to_dict()
    roles = user_data.get("roles", {})

    # Remove from both owner and staff lists
    if "owner" in roles and tenant_id in roles["owner"]:
        roles["owner"].remove(tenant_id)
    if "staff" in roles and tenant_id in roles["staff"]:
        roles["staff"].remove(tenant_id)

    db.collection("users").document(staff_uid).update({"roles": roles})

    return {"success": True, "message": f"Staff member {staff_uid} removed"}
