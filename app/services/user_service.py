import secrets
import string
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.passwords import hash_password, verify_password
from app.db.orm import User, UserRole, Wallet
from app.models.user import (
    AdminAccountCreateRequest,
    AdminAccountResponse,
    AdminPasswordResetResponse,
    MeResponse,
    OwnerRegisterRequest,
    PlayerRegisterRequest,
)


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


def admin_login(db: Session, email: str, password: str) -> MeResponse:
    user = db.query(User).filter(User.email == email.lower()).first()
    if not user or not user.password_hash or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return get_me(db, user.uid)


def _generate_temp_password() -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(12))


def create_admin_account(db: Session, req: AdminAccountCreateRequest) -> MeResponse:
    if db.query(User).filter(User.email == req.email.lower()).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")
    uid = uuid.uuid4().hex
    _create_user_row(db, uid, req.display_name, req.phone, is_player=False)
    db.flush()
    user = db.query(User).filter(User.uid == uid).first()
    user.email = req.email.lower()
    user.password_hash = hash_password(req.password)
    db.commit()
    return get_me(db, uid)


def list_admin_accounts(db: Session) -> list[AdminAccountResponse]:
    users = db.query(User).filter(User.password_hash.isnot(None)).order_by(User.created_at.desc()).all()
    results = []
    for user in users:
        roles = db.query(UserRole).filter(UserRole.uid == user.uid).all()
        results.append(AdminAccountResponse(
            uid=user.uid,
            email=user.email,
            display_name=user.display_name,
            is_superadmin=user.is_superadmin,
            owner_of=[r.tenant_id for r in roles if r.role_type == "owner"],
            staff_of=[r.tenant_id for r in roles if r.role_type == "staff"],
            created_at=user.created_at.isoformat(),
        ))
    return results


def reset_admin_password(db: Session, uid: str) -> AdminPasswordResetResponse:
    user = db.query(User).filter(User.uid == uid).first()
    if not user or not user.password_hash:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin account not found")
    new_password = _generate_temp_password()
    user.password_hash = hash_password(new_password)
    db.commit()
    return AdminPasswordResetResponse(uid=user.uid, email=user.email, new_password=new_password)


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
        email=user.email,
        is_player=user.is_player,
        is_superadmin=user.is_superadmin,
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
