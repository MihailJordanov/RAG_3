from pydantic import BaseModel, ConfigDict


class GoogleLoginRequest(BaseModel):
    credential: str


class UserResponse(BaseModel):
    id: str
    name: str | None = None
    email: str | None = None
    is_guest: bool

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse