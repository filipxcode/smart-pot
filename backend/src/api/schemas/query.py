from pydantic import BaseModel, Field

from agent.retrieval.rag_search import ChunkHit


class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)


class QueryResponse(BaseModel):
    answer: str
    sources: list[ChunkHit]
