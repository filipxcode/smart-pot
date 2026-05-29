import logging
from contextlib import asynccontextmanager

import logfire
from fastapi import FastAPI
from openai import AsyncOpenAI
from sqlalchemy import text

from config.settings import get_settings

_settings = get_settings()
logfire.configure(
    token=_settings.LOGFIRE_TOKEN.get_secret_value() if _settings.LOGFIRE_TOKEN else None,
    service_name=_settings.LOGFIRE_SERVICE_NAME,
    environment=_settings.LOGFIRE_ENVIRONMENT,
    send_to_logfire="if-token-present",
    console=False,
)
logfire.instrument_pydantic_ai()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logfire.LogfireLoggingHandler(), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

import api.models
from api.auth import auth_backend, fastapi_users
from api.base import Base
from api.db import engine
from api.routes.document import router as document_router
from api.routes.query import router as query_router
from api.schemas.user import UserCreate, UserRead, UserUpdate


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Startup: initializing database schema")
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Startup: database ready, initializing OpenAI client")
    app.state.openai_client = AsyncOpenAI(api_key=get_settings().OPENAI_API_KEY)
    logger.info("Startup complete")
    try:
        yield
    finally:
        logger.info("Shutdown: closing OpenAI client")
        await app.state.openai_client.close()


app = FastAPI(lifespan=lifespan)

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)
app.include_router(document_router)
app.include_router(query_router)
