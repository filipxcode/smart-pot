import logging

from fastapi import APIRouter, Depends
from openai import AsyncOpenAI
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)
from sqlalchemy.ext.asyncio import AsyncSession

from agent.orchestrator import run_turn
from agent.deps import ChatDeps
from api.auth import current_active_user
from api.db import get_async_session
from api.dependencies import get_openai_client
from api.models.user import User
from api.schemas.query import ChatTurn, QueryRequest, QueryResponse
from api.service.devices import get_primary_device
from config.settings import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["query"])


def _to_messages(history: list[ChatTurn]) -> list[ModelMessage]:
    messages: list[ModelMessage] = []
    for turn in history:
        if turn.role == "user":
            messages.append(ModelRequest(parts=[UserPromptPart(content=turn.content)]))
        else:
            messages.append(ModelResponse(parts=[TextPart(content=turn.content)]))
    return messages


def _to_turns(messages: list[ModelMessage]) -> list[ChatTurn]:
    turns: list[ChatTurn] = []
    for msg in messages:
        for part in msg.parts:
            if isinstance(part, UserPromptPart) and isinstance(part.content, str):
                turns.append(ChatTurn(role="user", content=part.content))
            elif isinstance(part, TextPart):
                turns.append(ChatTurn(role="assistant", content=part.content))
    return turns


@router.post("", response_model=QueryResponse)
async def query(
    body: QueryRequest,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
    openai: AsyncOpenAI = Depends(get_openai_client),
):
    settings = get_settings()
    # MVP: pick the user's primary device server-side. TODO: let the client pass device_id (multi-device support).
    device = await get_primary_device(user.id, session)
    deps = ChatDeps(
        session=session,
        openai=openai,
        user_id=user.id,
        device_id=device.id,
        embedding_model=settings.EMBEDDING_MODEL,
    )
    answer, sources, new_history = await run_turn(
        query=body.query, deps=deps, history=_to_messages(body.history)
    )
    logger.info("query handled: user=%s sources=%d", user.id, len(sources))
    return QueryResponse(answer=answer, sources=sources, history=_to_turns(new_history))
