from uuid import UUID

from openai import AsyncOpenAI
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from agent.ingestion.embeddings import embed_one

logger = logging.getLogger(__name__)
RRF_K = 60

_HYBRID_SQL = text("""
WITH dense AS (
    SELECT id, ROW_NUMBER() OVER () AS rank
    FROM (
        SELECT c.id
        FROM chunks c
        JOIN documents d ON d.id = c.document_id
        WHERE d.owner_id = :owner_id
        ORDER BY c.embedding <=> CAST(:qvec AS vector)
        LIMIT :candidates
    ) t
),
sparse AS (
    SELECT id, ROW_NUMBER() OVER () AS rank
    FROM (
        SELECT c.id
        FROM chunks c
        JOIN documents d ON d.id = c.document_id
        CROSS JOIN to_tsquery(
            'simple',
            NULLIF(replace(websearch_to_tsquery('simple', :qtext)::text, '&', '|'), '')
        ) AS q
        WHERE d.owner_id = :owner_id
          AND to_tsvector('simple', c.text) @@ q
        ORDER BY ts_rank_cd(to_tsvector('simple', c.text), q) DESC
        LIMIT :candidates
    ) t
),
fused AS (
    SELECT id, SUM(1.0 / (:rrf_k + rank)) AS score
    FROM (
        SELECT id, rank FROM dense
        UNION ALL
        SELECT id, rank FROM sparse
    ) u
    GROUP BY id
)
SELECT c.id           AS chunk_id,
       c.document_id  AS document_id,
       c.text         AS chunk_text,
       d.title        AS document_title,
       f.score        AS similarity,
       1 - (c.embedding <=> CAST(:qvec AS vector)) AS cosine_similarity
FROM fused f
JOIN chunks c ON c.id = f.id
JOIN documents d ON d.id = c.document_id
ORDER BY f.score DESC
LIMIT :top_k
""")

class ChunkHit(BaseModel):
    chunk_id: int
    document_id: int
    chunk_text: str
    document_title: str
    similarity: float  # RRF fusion score (dense + sparse), not a vector distance
    cosine_similarity: float  # 1 - cosine distance between query and chunk embedding


async def hybrid_search(
    session: AsyncSession,
    openai_client: AsyncOpenAI,
    embedding_model: str,
    query: str,
    owner_id: UUID,
    top_k: int = 20,
    candidates: int = 100,
) -> list[ChunkHit]:
    """Low latency raw SQL hybrid search function, scoped to a single owner."""
    logger.info("hybrid_search start: query=%r owner=%s top_k=%d candidates=%d", query, owner_id, top_k, candidates)
    embedding = await embed_one(openai_client, embedding_model, [query])
    qvec = "[" + ",".join(map(str, embedding)) + "]"
    result = await session.execute(
        _HYBRID_SQL,
        {
            "qvec": qvec,
            "qtext": query,
            "owner_id": owner_id,
            "candidates": candidates,
            "top_k": top_k,
            "rrf_k": RRF_K,
        },
    )
    hits = [ChunkHit.model_validate(row) for row in result.mappings().all()]
    logger.info("hybrid_search done: hits=%d", len(hits))
    return hits
