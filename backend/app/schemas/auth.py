from pydantic import BaseModel


class AuthStatus(BaseModel):
    is_authenticated: bool
    hh_connected: bool
    hh_user_id: str | None = None


class HHTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str
