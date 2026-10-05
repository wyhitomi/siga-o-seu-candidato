import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.connectors.base import SourceUnavailableError
from app.core.cache import get_redis
from app.core.db import get_session, get_session_factory
from app.modules.auth.deps import require_admin
from app.modules.parliamentarians import service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
    responses={401: {"description": "Não autenticado"}},
)


class SyncResult(BaseModel):
    stored: int


class SyncScheduled(BaseModel):
    detail: str = "Carga agendada. Acompanhe pelos logs."


@router.post("/sync/senators", summary="Atualizar senadores agora")
async def sync_senators(
    session: AsyncSession = Depends(get_session), redis: Redis = Depends(get_redis)
) -> SyncResult:
    try:
        return SyncResult(stored=await service.sync_senators(session, redis))
    except SourceUnavailableError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


async def _run_state_deputies_sync(
    factory: async_sessionmaker[AsyncSession], redis: Redis, uf: str | None
) -> None:
    async with factory() as session:
        try:
            await service.sync_state_deputies(session, redis, uf)
        except SourceUnavailableError:
            logger.exception("State deputies sync failed (uf=%s)", uf)


@router.post(
    "/sync/state-deputies",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Carregar deputados estaduais do TSE (em segundo plano)",
)
async def sync_state_deputies(
    background: BackgroundTasks,
    uf: str | None = Query(None, pattern=r"^[A-Za-z]{2}$"),
    factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
    redis: Redis = Depends(get_redis),
) -> SyncScheduled:
    background.add_task(_run_state_deputies_sync, factory, redis, uf.upper() if uf else None)
    return SyncScheduled()
