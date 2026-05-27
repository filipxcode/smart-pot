import logging
from uuid import UUID

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from agent.retrieval.rag_search import ChunkHit, hybrid_search

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a helpful assistant answering questions based on the user's documents. "
    "Use ONLY the provided context to answer. If the context does not contain the answer, "
    "say you don't know. Cite document titles when relevant."
)


async def answer_query(
    query: str,
    session: AsyncSession,
    openai: AsyncOpenAI,
    embedding_model: str,
    chat_model: str,
    top_k: int,
    owner_id: UUID,
) -> tuple[str, list[ChunkHit]]:
    hits = await hybrid_search(
        session=session,
        openai_client=openai,
        embedding_model=embedding_model,
        query=query,
        owner_id=owner_id,
        top_k=top_k,
    )
    if not hits:
        return "I don't know — no relevant context was found in your documents.", []

    context = "\n\n---\n\n".join(
        f"[{i + 1}] {h.document_title}\n{h.chunk_text}" for i, h in enumerate(hits)
    )
    user_message = f"Context:\n{context}\n\nQuestion: {query}"

    logger.info("answer_query: query=%r hits=%d model=%s", query, len(hits), chat_model)
    response = await openai.chat.completions.create(
        model=chat_model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )
    answer = response.choices[0].message.content or ""
    logger.info(
        "answer_query done: answer_chars=%d tokens_prompt=%s tokens_completion=%s",
        len(answer),
        getattr(response.usage, "prompt_tokens", None),
        getattr(response.usage, "completion_tokens", None),
    )
    return answer, hits
