import re
from urllib.parse import parse_qs, urlparse

import httpx
import respx
from fakeredis import FakeAsyncRedis
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.auth.models import AdminUser
from tests.conftest import FakeMailer
from tests.test_senators import PAYLOAD, SENADO_URL

ADMIN_EMAIL = "admin@example.com"


async def _create_admin(session: AsyncSession, active: bool = True) -> AdminUser:
    admin = AdminUser(email=ADMIN_EMAIL, is_active=active)
    session.add(admin)
    await session.commit()
    return admin


def _token_from(mailer: FakeMailer) -> str:
    link = re.search(r"https?://\S+", mailer.sent[-1][2]).group(0)  # type: ignore[union-attr]
    return parse_qs(urlparse(link).query)["token"][0]


async def _login(client: AsyncClient, mailer: FakeMailer) -> str:
    await client.post("/api/v1/auth/magic-link", json={"email": ADMIN_EMAIL.upper()})
    response = await client.post("/api/v1/auth/verify", json={"token": _token_from(mailer)})
    assert response.status_code == 200
    return response.json()["access_token"]


async def test_full_login_flow(
    client: AsyncClient, session: AsyncSession, mailer: FakeMailer
) -> None:
    await _create_admin(session)

    token = await _login(client, mailer)
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert mailer.sent[0][0] == ADMIN_EMAIL
    assert me.status_code == 200
    assert me.json()["email"] == ADMIN_EMAIL
    assert me.json()["last_login_at"] is not None


async def test_link_is_single_use(
    client: AsyncClient, session: AsyncSession, mailer: FakeMailer
) -> None:
    await _create_admin(session)
    await client.post("/api/v1/auth/magic-link", json={"email": ADMIN_EMAIL})
    token = _token_from(mailer)

    first = await client.post("/api/v1/auth/verify", json={"token": token})
    second = await client.post("/api/v1/auth/verify", json={"token": token})

    assert first.status_code == 200
    assert second.status_code == 401


async def test_unknown_or_inactive_email_gets_same_response_and_no_email(
    client: AsyncClient, session: AsyncSession, mailer: FakeMailer
) -> None:
    await _create_admin(session, active=False)

    inactive = await client.post("/api/v1/auth/magic-link", json={"email": ADMIN_EMAIL})
    unknown = await client.post("/api/v1/auth/magic-link", json={"email": "x@example.com"})

    assert inactive.status_code == unknown.status_code == 202
    assert inactive.json() == unknown.json()
    assert mailer.sent == []


async def test_magic_link_is_rate_limited(client: AsyncClient) -> None:
    limit = get_settings().magic_link_max_requests
    for _ in range(limit):
        ok = await client.post("/api/v1/auth/magic-link", json={"email": ADMIN_EMAIL})
        assert ok.status_code == 202

    blocked = await client.post("/api/v1/auth/magic-link", json={"email": ADMIN_EMAIL})
    assert blocked.status_code == 429


async def test_magic_link_token_expires(
    client: AsyncClient, session: AsyncSession, mailer: FakeMailer, redis: FakeAsyncRedis
) -> None:
    await _create_admin(session)
    await client.post("/api/v1/auth/magic-link", json={"email": ADMIN_EMAIL})
    (key,) = await redis.keys("auth:magic:*")
    assert 0 < await redis.ttl(key) <= get_settings().magic_link_ttl_minutes * 60


async def test_admin_routes_require_token(client: AsyncClient) -> None:
    missing = await client.post("/api/v1/admin/sync/senators")
    forged = await client.post(
        "/api/v1/admin/sync/senators", headers={"Authorization": "Bearer not-a-jwt"}
    )
    assert missing.status_code == forged.status_code == 401


async def test_deactivated_admin_token_is_rejected(
    client: AsyncClient, session: AsyncSession, mailer: FakeMailer
) -> None:
    admin = await _create_admin(session)
    token = await _login(client, mailer)
    admin.is_active = False
    await session.commit()

    response = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


@respx.mock
async def test_admin_can_sync_senators(
    client: AsyncClient, session: AsyncSession, mailer: FakeMailer
) -> None:
    respx.get(SENADO_URL).mock(return_value=httpx.Response(200, json=PAYLOAD))
    await _create_admin(session)
    token = await _login(client, mailer)

    response = await client.post(
        "/api/v1/admin/sync/senators", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json() == {"stored": 2}


@respx.mock
async def test_admin_sync_senators_reports_source_failure(
    client: AsyncClient, session: AsyncSession, mailer: FakeMailer
) -> None:
    respx.get(SENADO_URL).mock(return_value=httpx.Response(503))
    await _create_admin(session)
    token = await _login(client, mailer)

    response = await client.post(
        "/api/v1/admin/sync/senators", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 502
