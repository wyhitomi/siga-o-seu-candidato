"""create parliamentarians

Revision ID: 0001
Revises:
Create Date: 2026-10-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.create_table(
        "parliamentarians",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("house", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("source_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("search_name", sa.String(length=512), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column("party", sa.String(length=32), nullable=True),
        sa.Column("uf", sa.String(length=2), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("photo_url", sa.String(length=512), nullable=True),
        sa.Column("profile_url", sa.String(length=512), nullable=True),
        sa.Column("mandate_start", sa.Date(), nullable=True),
        sa.Column("mandate_end", sa.Date(), nullable=True),
        sa.Column("raw", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_parliamentarians")),
        sa.UniqueConstraint("house", "source_id", name="uq_parliamentarians_house_source_id"),
    )
    op.create_index("ix_parliamentarians_house_uf", "parliamentarians", ["house", "uf"])
    op.create_index(
        "ix_parliamentarians_search_name_trgm",
        "parliamentarians",
        ["search_name"],
        postgresql_using="gin",
        postgresql_ops={"search_name": "gin_trgm_ops"},
    )


def downgrade() -> None:
    op.drop_table("parliamentarians")
