from datetime import date, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, Date, DateTime, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin


class House(StrEnum):
    SENADO = "senado"
    ASSEMBLEIA_ESTADUAL = "assembleia_estadual"


class Parliamentarian(TimestampMixin, Base):
    __tablename__ = "parliamentarians"
    __table_args__ = (
        UniqueConstraint("house", "source_id", name="uq_parliamentarians_house_source_id"),
        Index("ix_parliamentarians_house_uf", "house", "uf"),
        Index(
            "ix_parliamentarians_search_name_trgm",
            "search_name",
            postgresql_using="gin",
            postgresql_ops={"search_name": "gin_trgm_ops"},
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    house: Mapped[str] = mapped_column(String(32))
    source: Mapped[str] = mapped_column(String(32))
    source_id: Mapped[str] = mapped_column(String(64))

    name: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    search_name: Mapped[str] = mapped_column(String(512))
    role: Mapped[str] = mapped_column(String(64))
    party: Mapped[str | None] = mapped_column(String(32))
    uf: Mapped[str] = mapped_column(String(2))
    status: Mapped[str | None] = mapped_column(String(64))

    email: Mapped[str | None] = mapped_column(String(255))
    photo_url: Mapped[str | None] = mapped_column(String(512))
    profile_url: Mapped[str | None] = mapped_column(String(512))
    mandate_start: Mapped[date | None] = mapped_column(Date)
    mandate_end: Mapped[date | None] = mapped_column(Date)

    raw: Mapped[dict[str, Any]] = mapped_column(JSON().with_variant(JSONB, "postgresql"))
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
