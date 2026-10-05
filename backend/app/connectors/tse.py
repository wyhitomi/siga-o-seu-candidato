"""TSE open data: elected state and district deputies.

Source: "Candidatos" dataset (consulta_cand_<ano>.zip), one CSV per UF,
`;`-separated and Latin-1 encoded. Docs: https://dadosabertos.tse.jus.br
"""

import asyncio
import csv
import io
import tempfile
import zipfile
from collections.abc import Iterator
from datetime import date
from pathlib import Path
from typing import IO

import httpx

from app.connectors.base import ParliamentarianRecord, SourceUnavailableError
from app.core.config import get_settings
from app.core.text import title_name

SOURCE = "tse"
ROLES = {"7": "Deputado(a) Estadual", "8": "Deputado(a) Distrital"}
NULL_VALUES = {"", "#NULO#", "#NE#", "#NULO", "#NE"}

# Only public-interest fields are kept: no CPF, voter ID, birth date or personal e-mail.
KEPT_FIELDS = (
    "ANO_ELEICAO",
    "SG_UF",
    "DS_CARGO",
    "NR_CANDIDATO",
    "SQ_CANDIDATO",
    "NM_URNA_CANDIDATO",
    "SG_PARTIDO",
    "NM_PARTIDO",
    "DS_SIT_TOT_TURNO",
)


async def fetch_elected_state_deputies(
    client: httpx.AsyncClient, year: int, uf: str | None = None
) -> list[ParliamentarianRecord]:
    url = get_settings().tse_consulta_cand_url.format(year=year)
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / f"consulta_cand_{year}.zip"
        try:
            async with client.stream("GET", url) as response:
                response.raise_for_status()
                with archive.open("wb") as fh:
                    async for chunk in response.aiter_bytes():
                        fh.write(chunk)
        except httpx.HTTPError as exc:
            raise SourceUnavailableError(f"TSE dataset unavailable: {exc}") from exc
        return await asyncio.to_thread(parse_elected_state_deputies, archive, year, uf)


def parse_elected_state_deputies(
    archive: Path, year: int, uf: str | None = None
) -> list[ParliamentarianRecord]:
    try:
        with zipfile.ZipFile(archive) as zf:
            return [
                record
                for name in _csv_members(zf, year, uf)
                for record in _parse_csv(zf.open(name), year)
            ]
    except zipfile.BadZipFile as exc:
        raise SourceUnavailableError("TSE dataset is not a valid zip file") from exc


def _csv_members(zf: zipfile.ZipFile, year: int, uf: str | None) -> list[str]:
    prefix = f"consulta_cand_{year}_"
    members = [
        n
        for n in zf.namelist()
        if n.startswith(prefix) and n.endswith(".csv") and not n.endswith("_BRASIL.csv")
    ]
    if uf:
        members = [n for n in members if n == f"{prefix}{uf.upper()}.csv"]
    if not members:
        raise SourceUnavailableError(f"No candidate file for year={year} uf={uf}")
    return members


def _parse_csv(raw: IO[bytes], year: int) -> Iterator[ParliamentarianRecord]:
    text = io.TextIOWrapper(raw, encoding="latin-1", newline="")
    for row in csv.DictReader(text, delimiter=";"):
        role = ROLES.get(row.get("CD_CARGO", ""))
        status = _clean(row.get("DS_SIT_TOT_TURNO"))
        if role is None or not status or not status.startswith("ELEITO"):
            continue
        ballot_name = _clean(row.get("NM_URNA_CANDIDATO")) or row["NM_CANDIDATO"]
        full_name = _clean(row.get("NM_SOCIAL_CANDIDATO")) or row["NM_CANDIDATO"]
        yield ParliamentarianRecord(
            source=SOURCE,
            source_id=row["SQ_CANDIDATO"],
            name=title_name(ballot_name),
            full_name=title_name(full_name),
            role=role,
            uf=row["SG_UF"],
            party=_clean(row.get("SG_PARTIDO")),
            status=status.capitalize(),
            mandate_start=date(year + 1, 2, 1),
            mandate_end=date(year + 5, 1, 31),
            raw={k: row[k] for k in KEPT_FIELDS if k in row},
        )


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return None if value in NULL_VALUES else value
