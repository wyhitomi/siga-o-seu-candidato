from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import Select, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.base import ParliamentarianRecord
from app.core.db import as_utc
from app.core.text import normalize
from app.modules.parliamentarians.models import House, Parliamentarian
from app.modules.parliamentarians.schemas import SearchParams


def _filtered(house: House, params: SearchParams) -> Select[tuple[Parliamentarian]]:
    stmt = select(Parliamentarian).where(Parliamentarian.house == house)
    if params.q:
        for term in normalize(params.q).split():
            stmt = stmt.where(Parliamentarian.search_name.contains(term, autoescape=True))
    if params.uf:
        stmt = stmt.where(Parliamentarian.uf == params.uf)
    if params.party:
        stmt = stmt.where(func.upper(Parliamentarian.party) == params.party)
    return stmt


async def search(
    session: AsyncSession, house: House, params: SearchParams
) -> tuple[Sequence[Parliamentarian], int]:
    stmt = _filtered(house, params)
    total = await session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    page = stmt.order_by(Parliamentarian.search_name, Parliamentarian.id)
    page = page.offset((params.page - 1) * params.page_size).limit(params.page_size)
    return (await session.scalars(page)).all(), total


async def get(
    session: AsyncSession, house: House, parliamentarian_id: int
) -> Parliamentarian | None:
    stmt = select(Parliamentarian).where(
        Parliamentarian.house == house, Parliamentarian.id == parliamentarian_id
    )
    return await session.scalar(stmt)


async def latest_fetch(session: AsyncSession, house: House) -> datetime | None:
    value = await session.scalar(
        select(func.max(Parliamentarian.fetched_at)).where(Parliamentarian.house == house)
    )
    return as_utc(value) if value else None


async def replace_snapshot(
    session: AsyncSession,
    house: House,
    records: Sequence[ParliamentarianRecord],
    fetched_at: datetime,
    uf: str | None = None,
) -> int:
    """Upsert `records` and remove rows of the same house (and UF) missing from them."""
    scope = select(Parliamentarian).where(Parliamentarian.house == house)
    if uf:
        scope = scope.where(Parliamentarian.uf == uf)
    existing = {p.source_id: p for p in (await session.scalars(scope)).all()}

    seen: set[str] = set()
    for record in records:
        if record.source_id in seen:
            continue
        seen.add(record.source_id)
        row = existing.get(record.source_id) or Parliamentarian(
            house=house, source_id=record.source_id
        )
        row.source = record.source
        row.name = record.name
        row.full_name = record.full_name
        row.search_name = normalize(f"{record.name} {record.full_name}")
        row.role = record.role
        row.party = record.party
        row.uf = record.uf
        row.status = record.status
        row.email = record.email
        row.photo_url = record.photo_url
        row.profile_url = record.profile_url
        row.mandate_start = record.mandate_start
        row.mandate_end = record.mandate_end
        row.raw = record.raw
        row.fetched_at = fetched_at
        session.add(row)

    stale_ids = [p.id for source_id, p in existing.items() if source_id not in seen]
    if stale_ids:
        await session.execute(delete(Parliamentarian).where(Parliamentarian.id.in_(stale_ids)))
    await session.commit()
    return len(seen)
