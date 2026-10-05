"""Shared pieces for public data source connectors.

Connectors only talk to external sources and return `ParliamentarianRecord`s;
persistence and freshness decisions belong to the service layer.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import get_settings

USER_AGENT = "SigaOSeuCandidato/0.1 (+https://github.com/wyhitomi/siga-o-seu-candidato)"


class SourceUnavailableError(Exception):
    """The external source could not be reached or returned unusable data."""


@dataclass(frozen=True, slots=True)
class ParliamentarianRecord:
    source: str
    source_id: str
    name: str
    full_name: str
    role: str
    uf: str
    party: str | None = None
    status: str | None = None
    email: str | None = None
    photo_url: str | None = None
    profile_url: str | None = None
    mandate_start: date | None = None
    mandate_end: date | None = None
    raw: dict[str, Any] = field(default_factory=dict)


def build_http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=get_settings().http_timeout_seconds,
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
    )


def _is_server_error(exc: BaseException) -> bool:
    return isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code >= 500


retry_transient = retry(
    retry=retry_if_exception_type(httpx.TransportError) | retry_if_exception(_is_server_error),
    stop=stop_after_attempt(get_settings().http_retry_attempts),
    wait=wait_exponential(multiplier=0.5, max=5),
    reraise=True,
)


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None
