"""Passwordless admin login: single-use e-mail link exchanged for a short-lived JWT."""

import hashlib
import secrets
from datetime import timedelta
from urllib.parse import urlencode

import jwt
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import get_settings
from app.core.db import utcnow
from app.core.email import Mailer
from app.modules.auth.models import AdminUser

JWT_ALGORITHM = "HS256"
JWT_AUDIENCE = "siga-admin"
JWT_ISSUER = "siga-api"


class RateLimitedError(Exception):
    pass


class InvalidTokenError(Exception):
    pass


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


async def _get_active_admin(session: AsyncSession, email: str) -> AdminUser | None:
    return await session.scalar(
        select(AdminUser).where(AdminUser.email == email.lower(), AdminUser.is_active.is_(True))
    )


async def check_rate_limit(redis: Redis, email: str) -> None:
    settings = get_settings()
    key = f"auth:ratelimit:{_digest(email.lower())}"
    attempts = await redis.incr(key)
    if attempts == 1:
        await redis.expire(key, settings.magic_link_window_minutes * 60)
    if attempts > settings.magic_link_max_requests:
        raise RateLimitedError


async def send_magic_link(
    factory: async_sessionmaker[AsyncSession], redis: Redis, mailer: Mailer, email: str
) -> None:
    """Send a login link if `email` belongs to an active admin; silently no-op otherwise."""
    async with factory() as session:
        admin = await _get_active_admin(session, email)
    if admin is None:
        return
    settings = get_settings()
    token = secrets.token_urlsafe(32)
    await redis.set(
        f"auth:magic:{_digest(token)}", admin.id, ex=settings.magic_link_ttl_minutes * 60
    )
    link = f"{settings.frontend_url}/admin/verificar?{urlencode({'token': token})}"
    await mailer.send(
        admin.email,
        "Seu link de acesso — Siga o seu candidato",
        f"Olá!\n\nUse o link abaixo para entrar na área administrativa. Ele vale por "
        f"{settings.magic_link_ttl_minutes} minutos e só pode ser usado uma vez:\n\n{link}\n\n"
        "Se você não pediu este acesso, ignore este e-mail.",
    )


async def verify_magic_link(session: AsyncSession, redis: Redis, token: str) -> str:
    admin_id = await redis.getdel(f"auth:magic:{_digest(token)}")
    if admin_id is None:
        raise InvalidTokenError
    admin = await session.get(AdminUser, int(admin_id))
    if admin is None or not admin.is_active:
        raise InvalidTokenError
    admin.last_login_at = utcnow()
    await session.commit()
    return issue_access_token(admin)


def issue_access_token(admin: AdminUser) -> str:
    settings = get_settings()
    now = utcnow()
    claims = {
        "sub": str(admin.id),
        "email": admin.email,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_ttl_minutes),
        "aud": JWT_AUDIENCE,
        "iss": JWT_ISSUER,
    }
    return jwt.encode(claims, settings.jwt_secret.get_secret_value(), algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> int:
    try:
        claims = jwt.decode(
            token,
            get_settings().jwt_secret.get_secret_value(),
            algorithms=[JWT_ALGORITHM],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
        )
        return int(claims["sub"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise InvalidTokenError from exc
