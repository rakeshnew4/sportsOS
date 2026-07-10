from pydantic import BaseModel


class PlayerRegisterRequest(BaseModel):
    display_name: str
    phone: str


class OwnerRegisterRequest(BaseModel):
    display_name: str
    phone: str


class LoginRequest(BaseModel):
    phone: str


class MeResponse(BaseModel):
    uid: str
    display_name: str | None = None
    is_player: bool
    owner_of: list[str]
    staff_of: list[str]
