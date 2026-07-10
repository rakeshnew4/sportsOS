import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.orm import User, UserRole, Wallet
from app.models.user import MeResponse, OwnerRegisterRequest, PlayerRegisterRequest


def register_player(db: Session, req: PlayerRegisterRequest, uid: str | None = None) -> MeResponse:
    uid = uid or uuid.uuid4().hex
    _create_user_row(db, uid, req.display_name, req.phone, is_player=True)
    db.add(Wallet(uid=uid, balance=0.0, currency="INR"))
    db.commit()
    return get_me(db, uid)


def register_owner(db: Session, req: OwnerRegisterRequest, uid: str | None = None) -> MeResponse:
    uid = uid or uuid.uuid4().hex
    _create_user_row(db, uid, req.display_name, req.phone, is_player=False)
    db.commit()
    return get_me(db, uid)


def find_uid_by_phone(db: Session, phone: str) -> str | None:
    user = db.query(User).filter(User.phone == phone).first()
    return user.uid if user else None


def login(db: Session, phone: str) -> MeResponse:
    uid = find_uid_by_phone(db, phone)
    if uid is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No account with this phone number"
        )
    return get_me(db, uid)


def _create_user_row(db: Session, uid: str, display_name: str, phone: str, is_player: bool) -> None:
    if db.query(User).filter(User.uid == uid).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already registered")
    if db.query(User).filter(User.phone == phone).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone number already registered")
    db.add(User(
        uid=uid,
        display_name=display_name,
        phone=phone,
        is_player=is_player,
        created_at=datetime.now(timezone.utc),
    ))


def get_me(db: Session, uid: str) -> MeResponse:
    user = db.query(User).filter(User.uid == uid).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not registered")
    roles = db.query(UserRole).filter(UserRole.uid == uid).all()
    owner_of = [r.tenant_id for r in roles if r.role_type == "owner"]
    staff_of = [r.tenant_id for r in roles if r.role_type == "staff"]
    return MeResponse(
        uid=uid,
        display_name=user.display_name,
        is_player=user.is_player,
        owner_of=owner_of,
        staff_of=staff_of,
    )


def grant_owner_role(db: Session, uid: str, tenant_id: str) -> None:
    if not db.query(User).filter(User.uid == uid).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not registered")
    existing = (
        db.query(UserRole)
        .filter(UserRole.uid == uid, UserRole.role_type == "owner", UserRole.tenant_id == tenant_id)
        .first()
    )
    if not existing:
        db.add(UserRole(uid=uid, role_type="owner", tenant_id=tenant_id))


def grant_staff_role(db: Session, uid: str, tenant_id: str) -> None:
    if not db.query(User).filter(User.uid == uid).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not registered")
    existing = (
        db.query(UserRole)
        .filter(UserRole.uid == uid, UserRole.role_type == "staff", UserRole.tenant_id == tenant_id)
        .first()
    )
    if not existing:
        db.add(UserRole(uid=uid, role_type="staff", tenant_id=tenant_id))
