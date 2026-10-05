from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class MagicLinkRequest(BaseModel):
    email: EmailStr


class MagicLinkAccepted(BaseModel):
    detail: str = "Se o e-mail for de um administrador, você receberá um link de acesso."


class VerifyRequest(BaseModel):
    token: str = Field(min_length=20, max_length=200)


class AccessToken(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"  # noqa: S105 - OAuth2 token type, not a secret
    expires_in: int


class AdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    last_login_at: datetime | None
