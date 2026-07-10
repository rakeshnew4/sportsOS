from dataclasses import dataclass, field

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.db.orm import User, UserRole

bearer_scheme = HTTPBearer()


@dataclass
class CurrentUser:
    uid: str
    is_player: bool = False
    owner_of: list[str] = field(default_factory=list)
    staff_of: list[str] = field(default_factory=list)

    def can_manage(self, tenant_id: str) -> bool:
        return tenant_id in self.owner_of or tenant_id in self.staff_of


def _verify_uid(credentials: HTTPAuthorizationCredentials) -> str:
    """Resolve the bearer token to a uid.

    No real auth provider is wired up yet for this deployment — the bearer
    token is the uid directly.
    """
    if not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    return credentials.credentials


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> CurrentUser:
    uid = _verify_uid(credentials)
    user = db.query(User).filter(User.uid == uid).first()
    roles = db.query(UserRole).filter(UserRole.uid == uid).all()

    return CurrentUser(
        uid=uid,
        is_player=bool(user.is_player) if user else False,
        owner_of=[r.tenant_id for r in roles if r.role_type == "owner"],
        staff_of=[r.tenant_id for r in roles if r.role_type == "staff"],
    )


def require_venue_access(tenant_id: str, user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if not user.can_manage(tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have owner/staff access to this venue",
        )
    return user
