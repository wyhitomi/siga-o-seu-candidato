"""Senado Federal open data: senators currently in office.

Docs: https://legis.senado.leg.br/dadosabertos/docs/
"""

from typing import Any

import httpx

from app.connectors.base import (
    ParliamentarianRecord,
    SourceUnavailableError,
    parse_date,
    retry_transient,
)
from app.core.config import get_settings

SOURCE = "senado"


@retry_transient
async def _get_current_list(client: httpx.AsyncClient) -> dict[str, Any]:
    url = f"{get_settings().senado_base_url}/senador/lista/atual"
    response = await client.get(url, headers={"Accept": "application/json"})
    response.raise_for_status()
    return response.json()


async def fetch_current_senators(client: httpx.AsyncClient) -> list[ParliamentarianRecord]:
    try:
        payload = await _get_current_list(client)
    except (httpx.HTTPError, ValueError) as exc:
        raise SourceUnavailableError(f"Senado API unavailable: {exc}") from exc
    return parse_current_senators(payload)


def parse_current_senators(payload: dict[str, Any]) -> list[ParliamentarianRecord]:
    try:
        items = payload["ListaParlamentarEmExercicio"]["Parlamentares"]["Parlamentar"]
    except (KeyError, TypeError) as exc:
        raise SourceUnavailableError("Unexpected Senado payload shape") from exc
    if isinstance(items, dict):  # the API returns an object when there is a single item
        items = [items]
    return [_parse_senator(item) for item in items]


def _parse_senator(item: dict[str, Any]) -> ParliamentarianRecord:
    ident = item["IdentificacaoParlamentar"]
    mandate = item.get("Mandato") or {}
    first_term = mandate.get("PrimeiraLegislaturaDoMandato") or {}
    second_term = mandate.get("SegundaLegislaturaDoMandato") or {}
    return ParliamentarianRecord(
        source=SOURCE,
        source_id=str(ident["CodigoParlamentar"]),
        name=ident["NomeParlamentar"],
        full_name=ident.get("NomeCompletoParlamentar") or ident["NomeParlamentar"],
        role="Senador(a)",
        uf=ident.get("UfParlamentar") or mandate.get("UfParlamentar") or "",
        party=ident.get("SiglaPartidoParlamentar"),
        status=mandate.get("DescricaoParticipacao"),
        email=ident.get("EmailParlamentar"),  # institutional e-mail
        photo_url=ident.get("UrlFotoParlamentar"),
        profile_url=ident.get("UrlPaginaParlamentar"),
        mandate_start=parse_date(first_term.get("DataInicio")),
        mandate_end=parse_date(second_term.get("DataFim") or first_term.get("DataFim")),
        raw=item,
    )
