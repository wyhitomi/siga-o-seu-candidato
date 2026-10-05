from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import get_redis
from app.core.db import get_session
from app.modules.parliamentarians import repository, service
from app.modules.parliamentarians.models import House
from app.modules.parliamentarians.schemas import (
    ParliamentarianOut,
    ParliamentarianPage,
    SearchParams,
    search_params,
)

NOT_FOUND = {404: {"description": "Parlamentar não encontrado"}}

senators = APIRouter(prefix="/api/v1/senators", tags=["senators"])


async def _ensure_fresh_senators(session: AsyncSession, redis: Redis) -> None:
    try:
        await service.ensure_senators_fresh(session, redis)
    except service.DataNotReadyError as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Dados do Senado indisponíveis no momento. Tente novamente em instantes.",
            headers={"Retry-After": "60"},
        ) from exc


@senators.get(
    "",
    summary="Buscar senadores em exercício",
    responses={503: {"description": "Fonte indisponível e sem dados armazenados"}},
)
async def search_senators(
    params: SearchParams = Depends(search_params),
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
) -> ParliamentarianPage:
    await _ensure_fresh_senators(session, redis)
    return await service.search(session, redis, House.SENADO, params)


@senators.get("/{senator_id}", summary="Detalhar senador", responses=NOT_FOUND)
async def get_senator(
    senator_id: int, session: AsyncSession = Depends(get_session)
) -> ParliamentarianOut:
    row = await repository.get(session, House.SENADO, senator_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Senador não encontrado")
    return ParliamentarianOut.model_validate(row)
