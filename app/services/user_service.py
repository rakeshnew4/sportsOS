from datetime import UTC, datetime

from fastapi import HTTPException, status

from app.core.db import Client

from app.models.user import MeResponse, OwnerRegisterRequest, PlayerRegisterRequest


def register_player(db: Client, uid: str, req: PlayerRegisterRequest) -> None:
    _create_user_doc(db, uid, req.display_name, req.phone, is_player=True)
    player_ref = db.collection("players").document(uid)
    player_ref.set(
        {
            "display_name": req.display_name,
            "phone": req.phone,
            "created_at": datetime.now(UTC).isoformat(),
        }
    )
    player_ref.collection("wallet").document("wallet").set({"balance": 0})


def register_owner(db: Client, uid: str, req: OwnerRegisterRequest) -> None:
    _create_user_doc(db, uid, req.display_name, req.phone, is_player=False)


def _create_user_doc(db: Client, uid: str, display_name: str, phone: str, is_player: bool) -> None:
    user_ref = db.collection("users").document(uid)
    if user_ref.get().exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already registered"
        )
    user_ref.set(
        {
            "display_name": display_name,
            "phone": phone,
            "roles": {"player": is_player, "owner": [], "staff": []},
            "created_at": datetime.now(UTC).isoformat(),
        }
    )


def get_me(db: Client, uid: str) -> MeResponse:
    user_doc = db.collection("users").document(uid).get()
    if not user_doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not registered")
    data = user_doc.to_dict()
    roles = data.get("roles", {})
    return MeResponse(
        uid=uid,
        display_name=data.get("display_name"),
        is_player=bool(roles.get("player")),
        owner_of=list(roles.get("owner", [])),
        staff_of=list(roles.get("staff", [])),
    )


def grant_owner_role(db: Client, uid: str, tenant_id: str) -> None:
    user_ref = db.collection("users").document(uid)
    user_doc = user_ref.get()
    if not user_doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not registered")
    roles = user_doc.to_dict().get("roles", {})
    owner_of = set(roles.get("owner", []))
    owner_of.add(tenant_id)
    user_ref.update({"roles.owner": list(owner_of)})
