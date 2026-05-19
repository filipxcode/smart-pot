from pydantic import BaseModel, Field

from agent.retrieval.rag_search import ChunkHit


class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=20)


class QueryResponse(BaseModel):
    answer: str
    sources: list[ChunkHit]
