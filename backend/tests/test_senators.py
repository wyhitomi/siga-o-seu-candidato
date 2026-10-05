import json
from datetime import timedelta
from pathlib import Path

import httpx
import respx
from fakeredis import FakeAsyncRedis
from httpx import AsyncClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.senado import parse_current_senators
from app.core.config import get_settings
from app.core.db import utcnow
from app.modules.parliamentarians.models import House, Parliamentarian

PAYLOAD = json.loads((Path(__file__).parent / "fixtures/senado_lista_atual.json").read_text())
SENADO_URL = f"{get_settings().senado_base_url}/senador/lista/atual"


def test_parse_current_senators() -> None:
    records = parse_current_senators(PAYLOAD)
    assert [r.source_id for r in records] == ["5000", "5001"]
    jose = records[0]
    assert jose.uf == "SP"
    assert jose.party == "PXX"
    assert str(jose.mandate_start) == "2023-02-01"
    assert str(jose.mandate_end) == "2031-01-31"


def test_parse_single_item_object() -> None:
    single = {
        "ListaParlamentarEmExercicio": {
            "Parlamentares": {
                "Parlamentar": PAYLOAD["ListaParlamentarEmExercicio"]["Parlamentares"][
                    "Parlamentar"
                ][0]
            }
        }
    }
    assert len(parse_current_senators(single)) == 1


@respx.mock
async def test_search_loads_from_source_and_ignores_accents(client: AsyncClient) -> None:
    route = respx.get(SENADO_URL).mock(return_value=httpx.Response(200, json=PAYLOAD))

    response = await client.get("/api/v1/senators", params={"q": "jose"})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["name"] == "José Exemplo"
    assert route.call_count == 1


@respx.mock
async def test_filters_by_uf_and_party(client: AsyncClient) -> None:
    respx.get(SENADO_URL).mock(return_value=httpx.Response(200, json=PAYLOAD))

    by_uf = await client.get("/api/v1/senators", params={"uf": "mg"})
    by_party = await client.get("/api/v1/senators", params={"party": "pxx"})

    assert [i["name"] for i in by_uf.json()["items"]] == ["Maria Modelo"]
    assert [i["name"] for i in by_party.json()["items"]] == ["José Exemplo"]


@respx.mock
async def test_fresh_data_is_not_refetched_and_responses_are_cached(
    client: AsyncClient, redis: FakeAsyncRedis
) -> None:
    route = respx.get(SENADO_URL).mock(return_value=httpx.Response(200, json=PAYLOAD))

    await client.get("/api/v1/senators")
    await client.get("/api/v1/senators")

    assert route.call_count == 1
    assert len(await redis.keys("cache:senado:*")) == 1


@respx.mock
async def test_serves_stored_data_when_source_fails(
    client: AsyncClient, session: AsyncSession
) -> None:
    respx.get(SENADO_URL).mock(return_value=httpx.Response(200, json=PAYLOAD))
    await client.get("/api/v1/senators")
    await session.execute(update(Parliamentarian).values(fetched_at=utcnow() - timedelta(days=2)))
    await session.commit()
    respx.get(SENADO_URL).mock(return_value=httpx.Response(500))

    response = await client.get("/api/v1/senators", params={"uf": "SP"})

    assert response.status_code == 200
    assert response.json()["total"] == 1


@respx.mock
async def test_returns_503_when_source_fails_and_nothing_is_stored(client: AsyncClient) -> None:
    respx.get(SENADO_URL).mock(side_effect=httpx.ConnectError("down"))

    response = await client.get("/api/v1/senators")

    assert response.status_code == 503
    assert response.headers["retry-after"] == "60"


@respx.mock
async def test_get_senator_by_id(client: AsyncClient, session: AsyncSession) -> None:
    respx.get(SENADO_URL).mock(return_value=httpx.Response(200, json=PAYLOAD))
    await client.get("/api/v1/senators")
    senator_id = await session.scalar(
        select(Parliamentarian.id).where(
            Parliamentarian.house == House.SENADO, Parliamentarian.source_id == "5001"
        )
    )

    found = await client.get(f"/api/v1/senators/{senator_id}")
    missing = await client.get("/api/v1/senators/999999")

    assert found.json()["full_name"] == "Maria Aparecida Modelo"
    assert missing.status_code == 404


async def test_rejects_invalid_uf(client: AsyncClient) -> None:
    response = await client.get("/api/v1/senators", params={"uf": "São Paulo"})
    assert response.status_code == 422
