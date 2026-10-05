from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.cache import get_redis
from app.core.config import get_settings
from app.core.db import get_session, get_session_factory
from app.core.email import Mailer, get_mailer
from app.modules.auth import service
from app.modules.auth.deps import require_admin
from app.modules.auth.models import AdminUser
from app.modules.auth.schemas import (
    AccessToken,
    AdminOut,
    MagicLinkAccepted,
    MagicLinkRequest,
    VerifyRequest,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post(
    "/magic-link",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Solicitar link de acesso (somente administradores)",
    responses={429: {"description": "Muitas solicitações para este e-mail"}},
)
async def request_magic_link(
    body: MagicLinkRequest,
    background: BackgroundTasks,
    factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
    redis: Redis = Depends(get_redis),
    mailer: Mailer = Depends(get_mailer),
) -> MagicLinkAccepted:
    try:
        await service.check_rate_limit(redis, body.email)
    except service.RateLimitedError:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, detail="Muitas solicitações. Tente mais tarde."
        ) from None
    # Lookup and e-mail happen after the response so timing does not reveal admins.
    background.add_task(service.send_magic_link, factory, redis, mailer, body.email)
    return MagicLinkAccepted()


@router.post(
    "/verify",
    summary="Trocar o link de acesso por um token",
    responses={401: {"description": "Link inválido, expirado ou já utilizado"}},
)
async def verify(
    body: VerifyRequest,
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
) -> AccessToken:
    try:
        token = await service.verify_magic_link(session, redis, body.token)
    except service.InvalidTokenError:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="Link inválido ou expirado"
        ) from None
    return AccessToken(access_token=token, expires_in=get_settings().jwt_ttl_minutes * 60)


@router.get("/me", summary="Administrador autenticado")
async def me(admin: AdminUser = Depends(require_admin)) -> AdminOut:
    return AdminOut.model_validate(admin)
