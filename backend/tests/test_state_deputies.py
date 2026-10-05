import csv
import io
import zipfile
from pathlib import Path

import httpx
import pytest
import respx
from fakeredis import FakeAsyncRedis
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.base import SourceUnavailableError
from app.connectors.tse import parse_elected_state_deputies
from app.core.config import get_settings
from app.modules.parliamentarians import service
from tests.conftest import FakeMailer

YEAR = 2022
TSE_URL = get_settings().tse_consulta_cand_url.format(year=YEAR)
HEADER = [
    "ANO_ELEICAO", "SG_UF", "CD_CARGO", "DS_CARGO", "SQ_CANDIDATO", "NR_CANDIDATO",
    "NM_CANDIDATO", "NM_URNA_CANDIDATO", "NM_SOCIAL_CANDIDATO", "NR_CPF_CANDIDATO",
    "DT_NASCIMENTO", "NM_EMAIL", "SG_PARTIDO", "NM_PARTIDO", "DS_SIT_TOT_TURNO",
]  # fmt: skip


def _row(uf: str, cargo: str, sq: str, urna: str, party: str, situacao: str) -> list[str]:
    return [
        str(YEAR), uf, cargo, "DEPUTADO ESTADUAL", sq, "12345", f"{urna} COMPLETO", urna,
        "#NULO#", "12345678900", "01/01/1980", "pessoal@example.com", party,
        "PARTIDO X", situacao,
    ]  # fmt: skip


ROWS = {
    "SP": [
        _row("SP", "7", "250001", "JOÃO DA SILVA", "PXX", "ELEITO POR QP"),
        _row("SP", "7", "250002", "ANA SOUZA", "PYY", "SUPLENTE"),
        _row("SP", "6", "250003", "CARLOS FEDERAL", "PXX", "ELEITO POR QP"),
    ],
    "MG": [_row("MG", "7", "130001", "BEATRIZ LIMA", "PYY", "ELEITO POR MÉDIA")],
    "DF": [_row("DF", "8", "70001", "DÉBORA DISTRITAL", "PZZ", "ELEITO")],
}


def _zip_bytes() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        for uf, rows in [*ROWS.items(), ("BRASIL", [r for rs in ROWS.values() for r in rs])]:
            text = io.StringIO()
            writer = csv.writer(text, delimiter=";", quoting=csv.QUOTE_ALL)
            writer.writerows([HEADER, *rows])
            zf.writestr(f"consulta_cand_{YEAR}_{uf}.csv", text.getvalue().encode("latin-1"))
        zf.writestr("leiame.pdf", b"")
    return buffer.getvalue()


@pytest.fixture
def archive(tmp_path: Path) -> Path:
    path = tmp_path / "consulta_cand.zip"
    path.write_bytes(_zip_bytes())
    return path


def test_parse_keeps_only_elected_state_and_district_deputies(archive: Path) -> None:
    records = parse_elected_state_deputies(archive, YEAR)
    assert sorted(r.source_id for r in records) == ["130001", "250001", "70001"]


def test_parse_formats_names_and_drops_personal_data(archive: Path) -> None:
    (joao,) = parse_elected_state_deputies(archive, YEAR, uf="SP")
    assert joao.name == "João da Silva"
    assert joao.role == "Deputado(a) Estadual"
    assert str(joao.mandate_start) == "2023-02-01"
    assert "NR_CPF_CANDIDATO" not in joao.raw
    assert "NM_EMAIL" not in joao.raw
    assert "DT_NASCIMENTO" not in joao.raw
    assert joao.email is None


def test_parse_unknown_uf_fails(archive: Path) -> None:
    with pytest.raises(SourceUnavailableError):
        parse_elected_state_deputies(archive, YEAR, uf="XX")


@respx.mock
async def test_sync_and_search(
    client: AsyncClient, session: AsyncSession, redis: FakeAsyncRedis
) -> None:
    respx.get(TSE_URL).mock(return_value=httpx.Response(200, content=_zip_bytes()))

    assert await service.sync_state_deputies(session, redis) == 3

    by_name = await client.get("/api/v1/state-deputies", params={"q": "joao silva"})
    by_uf = await client.get("/api/v1/state-deputies", params={"uf": "df"})
    assert [i["name"] for i in by_name.json()["items"]] == ["João da Silva"]
    assert by_uf.json()["items"][0]["role"] == "Deputado(a) Distrital"

    detail = await client.get(f"/api/v1/state-deputies/{by_uf.json()['items'][0]['id']}")
    assert detail.json()["uf"] == "DF"


@respx.mock
async def test_sync_by_uf_only_replaces_that_uf(
    client: AsyncClient, session: AsyncSession, redis: FakeAsyncRedis
) -> None:
    respx.get(TSE_URL).mock(return_value=httpx.Response(200, content=_zip_bytes()))
    await service.sync_state_deputies(session, redis)
    await client.get("/api/v1/state-deputies")  # warm the cache

    assert await service.sync_state_deputies(session, redis, uf="SP") == 1

    response = await client.get("/api/v1/state-deputies")
    assert response.json()["total"] == 3


async def test_empty_search_returns_empty_page(client: AsyncClient) -> None:
    response = await client.get("/api/v1/state-deputies")
    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "page": 1, "page_size": 20}


@respx.mock
async def test_admin_schedules_state_deputies_sync(
    client: AsyncClient, session: AsyncSession, mailer: FakeMailer
) -> None:
    from tests.test_auth import _create_admin, _login

    respx.get(TSE_URL).mock(return_value=httpx.Response(200, content=_zip_bytes()))
    await _create_admin(session)
    token = await _login(client, mailer)

    response = await client.post(
        "/api/v1/admin/sync/state-deputies",
        params={"uf": "mg"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 202
    deputies = await client.get("/api/v1/state-deputies")
    assert [i["uf"] for i in deputies.json()["items"]] == ["MG"]
