from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Schema for login payload."""
    email: str
    password: str


class TokenResponse(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class RefreshRequest(BaseModel):
    """Schema for token refresh."""
    refresh_token: str
