from pydantic_ai import ModelRetry, RunContext

from agent.deps import ChatDeps
from agent.retrieval.rag_search import ChunkHit, hybrid_search


async def search_document(ctx: RunContext[ChatDeps], query: str) -> list[ChunkHit]:
    hits = await hybrid_search(
        session=ctx.deps.session,
        openai_client=ctx.deps.openai,
        embedding_model=ctx.deps.embedding_model,
        query=query,
        owner_id=ctx.deps.user_id,
    )
    if not hits:
        raise ModelRetry("Brak wyników — zmień zapytanie, w dokumentach nie ma takich informacji.")
    return hits
