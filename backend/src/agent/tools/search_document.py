from pydantic_ai import RunContext, ModelRetry
from agent.retrieval.rag_search import hybrid_search, ChunkHit
from agent.tool_agent import _tool_agent

@_tool_agent.tool
async def search_document(query: str, ctx: RunContext) -> ChunkHit:
    hits = await hybrid_search(
        session=ctx.deps.session,
        openai_client=ctx.deps.openai,
        embedding_model=ctx.deps.embedding_model,
        query=query,
        owner_id=ctx.deps.user_id,
        top_k=ctx.deps.top_k,
    )
    if not hits:
        return ModelRetry("Try to change a query, there is no sources!")
    return hits