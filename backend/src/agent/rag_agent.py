import logging

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage

from agent.deps import ChatDeps
from agent.prompts.prompts import PromptsOrganizer
from agent.retrieval.rag_search import ChunkHit, hybrid_search
from config.settings import get_settings

logger = logging.getLogger(__name__)

_rag_agent = Agent(
    get_settings().LLM_MODEL,
    output_type=str,
    system_prompt=PromptsOrganizer.RAG_SYSTEM,
)


async def rag_answer(
    query: str,
    deps: ChatDeps,
    history: list[ModelMessage] | None = None,
) -> tuple[str, list[ChunkHit]]:
    hits = await hybrid_search(
        session=deps.session,
        openai_client=deps.openai,
        embedding_model=deps.embedding_model,
        query=query,
        owner_id=deps.user_id,
        top_k=deps.top_k,
    )
    if not hits:
        return "I don't know — no relevant context was found in your documents.", []

    context = "\n\n---\n\n".join(
        f"[{i + 1}] {h.document_title}\n{h.chunk_text}" for i, h in enumerate(hits)
    )
    user_message = PromptsOrganizer.rag_user(context=context, query=query)

    logger.info("rag_answer: query=%r hits=%d", query, len(hits))
    result = await _rag_agent.run(user_message, message_history=history or [])
    answer = result.output
    logger.info("rag_answer done: answer_chars=%d", len(answer))
    return answer, hits
