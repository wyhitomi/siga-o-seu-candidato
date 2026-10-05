import logging
from datetime import timedelta

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors import senado, tse
from app.connectors.base import SourceUnavailableError, build_http_client
from app.core import cache
from app.core.config import get_settings
from app.core.db import utcnow
from app.modules.parliamentarians import repository
from app.modules.parliamentarians.models import House
from app.modules.parliamentarians.schemas import (
    ParliamentarianOut,
    ParliamentarianPage,
    SearchParams,
)

logger = logging.getLogger(__name__)


class DataNotReadyError(Exception):
    """No data stored yet and it could not be loaded right now."""


async def search(
    session: AsyncSession, redis: Redis, house: House, params: SearchParams
) -> ParliamentarianPage:
    key = await cache.cache_key(redis, house, params.model_dump())
    if cached := await redis.get(key):
        return ParliamentarianPage.model_validate_json(cached)

    rows, total = await repository.search(session, house, params)
    page = ParliamentarianPage(
        items=[ParliamentarianOut.model_validate(r) for r in rows],
        total=total,
        page=params.page,
        page_size=params.page_size,
    )
    await redis.set(key, page.model_dump_json(), ex=get_settings().search_cache_ttl_seconds)
    return page


async def sync_senators(session: AsyncSession, redis: Redis) -> int:
    async with build_http_client() as client:
        records = await senado.fetch_current_senators(client)
    count = await repository.replace_snapshot(session, House.SENADO, records, utcnow())
    await cache.invalidate(redis, House.SENADO)
    logger.info("Stored %d senators", count)
    return count


async def ensure_senators_fresh(session: AsyncSession, redis: Redis) -> None:
    """Refresh senators when stale; keep serving stored data if the source fails."""
    last = await repository.latest_fetch(session, House.SENADO)
    max_age = timedelta(hours=get_settings().senators_stale_after_hours)
    if last and utcnow() - last < max_age:
        return

    lock = "sync:senado"
    if not await cache.acquire_lock(redis, lock, ttl_seconds=120):
        if last is None:
            raise DataNotReadyError("Senators are being loaded")
        return
    try:
        await sync_senators(session, redis)
    except SourceUnavailableError:
        logger.warning("Senado source unavailable; serving stored data", exc_info=True)
        if last is None:
            raise DataNotReadyError("Senado source unavailable") from None
    finally:
        await cache.release_lock(redis, lock)


async def sync_state_deputies(session: AsyncSession, redis: Redis, uf: str | None = None) -> int:
    year = get_settings().tse_election_year
    async with build_http_client() as client:
        records = await tse.fetch_elected_state_deputies(client, year, uf)
    count = await repository.replace_snapshot(
        session, House.ASSEMBLEIA_ESTADUAL, records, utcnow(), uf=uf
    )
    await cache.invalidate(redis, House.ASSEMBLEIA_ESTADUAL)
    logger.info("Stored %d state deputies (uf=%s, year=%d)", count, uf or "all", year)
    return count
