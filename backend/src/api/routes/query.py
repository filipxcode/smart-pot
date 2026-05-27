import logging

from fastapi import APIRouter, Depends
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from agent.rag_agent import rag_answer
from agent.deps import ChatDeps
from api.auth import current_active_user
from api.db import get_async_session
from api.dependencies import get_openai_client
from api.models.user import User
from api.schemas.query import QueryRequest, QueryResponse
from config.settings import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=QueryResponse)
async def query(
    body: QueryRequest,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
    openai: AsyncOpenAI = Depends(get_openai_client),
):
    settings = get_settings()
    deps = ChatDeps(
        session=session,
        openai=openai,
        user_id=user.id,
        embedding_model=settings.EMBEDDING_MODEL,
        top_k=body.top_k or settings.QUERY_TOP_K,
    )
    answer, sources = await rag_answer(query=body.query, deps=deps)
    logger.info("query handled: user=%s top_k=%d", user.id, len(sources))
    return QueryResponse(answer=answer, sources=sources)
