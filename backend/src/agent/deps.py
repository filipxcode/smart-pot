from dataclasses import dataclass

from uuid import UUID
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class ChatDeps:
    session: AsyncSession
    openai: AsyncOpenAI
    user_id: UUID
    device_id: int
    embedding_model: str