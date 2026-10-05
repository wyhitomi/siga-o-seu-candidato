from functools import lru_cache
from typing import Literal

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_JWT_SECRET = "change-me"  # noqa: S105 - placeholder rejected in production


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: Literal["dev", "test", "prod"] = "dev"

    database_url: str = "postgresql+asyncpg://siga:siga@localhost:5432/siga"
    redis_url: str = "redis://localhost:6379/0"

    cors_origins: list[str] = ["http://localhost:3000"]
    frontend_url: str = "http://localhost:3000"

    # Admin auth
    jwt_secret: SecretStr = SecretStr(DEFAULT_JWT_SECRET)
    jwt_ttl_minutes: int = 60
    magic_link_ttl_minutes: int = 15
    magic_link_max_requests: int = 5
    magic_link_window_minutes: int = 15

    # E-mail (Mailpit in development)
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str | None = None
    smtp_password: SecretStr | None = None
    smtp_starttls: bool = False
    smtp_from: str = "Siga o seu candidato <nao-responda@sigaoseucandidato.local>"

    # Cache
    search_cache_ttl_seconds: int = 900

    # Data sources
    http_timeout_seconds: float = 30.0
    senado_base_url: str = "https://legis.senado.leg.br/dadosabertos"
    senators_stale_after_hours: int = 24
    tse_consulta_cand_url: str = (
        "https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/consulta_cand_{year}.zip"
    )
    tse_election_year: int = 2022

    @model_validator(mode="after")
    def _reject_default_secret_in_prod(self) -> "Settings":
        if self.env == "prod" and self.jwt_secret.get_secret_value() == DEFAULT_JWT_SECRET:
            raise ValueError("JWT_SECRET must be set in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
