from typing import Literal

from pydantic import BaseModel, Field

from agent.retrieval.rag_search import ChunkHit


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    history: list[ChatTurn] = Field(default_factory=list)


class QueryResponse(BaseModel):
    answer: str
    sources: list[ChunkHit]
    history: list[ChatTurn]
