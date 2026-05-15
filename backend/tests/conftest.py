import os
from collections.abc import AsyncGenerator

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///file::memory:?cache=shared&uri=true")
os.environ.setdefault("JWT_SECRET", "test-secret")

import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.auth import auth_backend, fastapi_users
from api.base import Base
from api.db import get_async_session
from api.models.device import Device  # noqa: F401  (register mappers)
from api.models.device_event import DeviceEvent  # noqa: F401
from api.models.metric import Metric  # noqa: F401
from api.models.user import User  # noqa: F401
from api.routes.device_event import router as device_event_router
from api.routes.devices import router as devices_router
from api.routes.metric import router as metric_router
from api.schemas.user import UserCreate, UserRead, UserUpdate


@pytest_asyncio.fixture
async def engine():
    eng = create_async_engine(
        "sqlite+aiosqlite:///file::memory:?cache=shared&uri=true",
        connect_args={"uri": True},
    )
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture
async def session_maker(engine):
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def app(session_maker) -> FastAPI:
    application = FastAPI()
    application.include_router(fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt")
    application.include_router(fastapi_users.get_register_router(UserRead, UserCreate), prefix="/auth")
    application.include_router(fastapi_users.get_users_router(UserRead, UserUpdate), prefix="/users")
    application.include_router(devices_router)
    application.include_router(metric_router)
    application.include_router(device_event_router)

    async def override_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_maker() as s:
            yield s

    application.dependency_overrides[get_async_session] = override_session
    return application


@pytest_asyncio.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


async def _register_and_login(client: AsyncClient, email: str, password: str = "Strong-Pass-1!") -> str:
    r = await client.post("/auth/register", json={"email": email, "password": password})
    assert r.status_code == 201, r.text
    r = await client.post(
        "/auth/jwt/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest_asyncio.fixture
async def auth_headers(client) -> dict[str, str]:
    token = await _register_and_login(client, "owner@test.dev")
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def other_auth_headers(client) -> dict[str, str]:
    token = await _register_and_login(client, "intruder@test.dev")
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def device(client, auth_headers) -> dict:
    r = await client.post(
        "/devices",
        json={"name": "Pot 1", "serial": "SN-001"},
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text
    return r.json()
