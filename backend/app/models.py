"""Import every ORM model so Alembic and tests see the full metadata."""

from app.modules.parliamentarians.models import Parliamentarian

__all__ = ["Parliamentarian"]
