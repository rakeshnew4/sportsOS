from dataclasses import dataclass, field

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth as firebase_auth

from app.core.firebase import get_firebase_app, get_firestore_client

bearer_scheme = HTTPBearer()


@dataclass
class CurrentUser:
    uid: str
    is_player: bool = False
    owner_of: list[str] = field(default_factory=list)
    staff_of: list[str] = field(default_factory=list)

    def can_manage(self, tenant_id: str) -> bool:
        return tenant_id in self.owner_of or tenant_id in self.staff_of


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> CurrentUser:
    get_firebase_app()
    try:
        decoded = firebase_auth.verify_id_token(credentials.credentials)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired auth token",
        ) from exc

    uid = decoded["uid"]
    db = get_firestore_client()
    user_doc = db.collection("users").document(uid).get()
    roles = user_doc.to_dict().get("roles", {}) if user_doc.exists else {}

    return CurrentUser(
        uid=uid,
        is_player=bool(roles.get("player")),
        owner_of=list(roles.get("owner", [])),
        staff_of=list(roles.get("staff", [])),
    )


def require_venue_access(tenant_id: str, user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if not user.can_manage(tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have owner/staff access to this venue",
        )
    return user
