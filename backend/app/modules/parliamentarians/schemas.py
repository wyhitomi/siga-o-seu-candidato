from datetime import date, datetime

from fastapi import Query
from pydantic import BaseModel, ConfigDict


class ParliamentarianOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    full_name: str
    role: str
    party: str | None
    uf: str
    status: str | None
    email: str | None
    photo_url: str | None
    profile_url: str | None
    mandate_start: date | None
    mandate_end: date | None
    source: str
    fetched_at: datetime


class ParliamentarianPage(BaseModel):
    items: list[ParliamentarianOut]
    total: int
    page: int
    page_size: int


class SearchParams(BaseModel):
    q: str | None = None
    uf: str | None = None
    party: str | None = None
    page: int = 1
    page_size: int = 20


def search_params(
    q: str | None = Query(None, min_length=2, max_length=100, description="Nome (sem acento ok)"),
    uf: str | None = Query(None, pattern=r"^[A-Za-z]{2}$", description="Sigla da UF, ex.: SP"),
    party: str | None = Query(None, max_length=32, description="Sigla do partido, ex.: PT"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> SearchParams:
    return SearchParams(
        q=q.strip() if q else None,
        uf=uf.upper() if uf else None,
        party=party.strip().upper() if party else None,
        page=page,
        page_size=page_size,
    )
