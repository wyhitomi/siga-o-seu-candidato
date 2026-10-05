import os

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-with-at-least-32-bytes!!")

from collections.abc import AsyncIterator  # noqa: E402

import pytest  # noqa: E402
from fakeredis import FakeAsyncRedis  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool  # noqa: E402

import app.models  # noqa: E402, F401
from app.core.cache import get_redis  # noqa: E402
from app.core.db import Base, get_session  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture
async def session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


@pytest.fixture
async def session(session_factory: async_sessionmaker[AsyncSession]) -> AsyncIterator[AsyncSession]:
    async with session_factory() as s:
        yield s


@pytest.fixture
async def redis() -> AsyncIterator[FakeAsyncRedis]:
    client = FakeAsyncRedis(decode_responses=True)
    yield client
    await client.aclose()


@pytest.fixture
def app(session_factory: async_sessionmaker[AsyncSession], redis: FakeAsyncRedis):  # type: ignore[no-untyped-def]
    application = create_app()

    async def _session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as s:
            yield s

    application.dependency_overrides[get_session] = _session
    application.dependency_overrides[get_redis] = lambda: redis
    return application


@pytest.fixture
async def client(app) -> AsyncIterator[AsyncClient]:  # type: ignore[no-untyped-def]
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
