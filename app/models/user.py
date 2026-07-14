from pydantic import BaseModel, EmailStr


class PlayerRegisterRequest(BaseModel):
    display_name: str
    phone: str


class OwnerRegisterRequest(BaseModel):
    display_name: str
    phone: str


class LoginRequest(BaseModel):
    phone: str


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class MeResponse(BaseModel):
    uid: str
    display_name: str | None = None
    email: str | None = None
    is_player: bool
    is_superadmin: bool = False
    owner_of: list[str]
    staff_of: list[str]


class AdminAccountCreateRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: str
    phone: str


class AdminAccountResponse(BaseModel):
    uid: str
    email: str | None = None
    display_name: str | None = None
    is_superadmin: bool
    owner_of: list[str]
    staff_of: list[str]
    created_at: str


class AdminPasswordResetResponse(BaseModel):
    uid: str
    email: str | None = None
    new_password: str
