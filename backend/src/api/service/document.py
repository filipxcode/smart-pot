import logging
from uuid import UUID

from fastapi import HTTPException
from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agent.ingestion.chunking import chunk_text
from agent.ingestion.embeddings import embed_batch
from agent.ingestion.parsers import parse_pdf
from api.models.chunk import Chunk
from api.models.document import DocumentModel
from config.settings import get_settings

logger = logging.getLogger(__name__)

async def create_pending_document(title: str, user_id: UUID, session: AsyncSession) -> DocumentModel:
    """Create the document row up front with status='processing' so the client can poll it."""
    doc = DocumentModel(title=title, raw_text="", owner_id=user_id, status="processing")
    session.add(doc)
    await session.commit()
    await session.refresh(doc)
    logger.info("create_pending_document: document_id=%s user=%s", doc.id, user_id)
    return doc


async def ingest_document(doc_id: int, data: bytes, session: AsyncSession, openai: AsyncOpenAI) -> None:
    """Parse, chunk, embed and fill an existing document. Sets status='success' on completion."""
    logger.info("ingest_document start: doc=%s size=%d", doc_id, len(data))
    doc = await session.get(DocumentModel, doc_id)
    if doc is None:
        logger.warning("ingest_document: document gone (doc=%s)", doc_id)
        return

    parsed_text = parse_pdf(data)
    if not parsed_text:
        raise ValueError("Empty or unreadable PDF")
    logger.info("ingest_document: parsed %d chars (doc=%s)", len(parsed_text), doc_id)

    chunked_text = chunk_text(parsed_text)
    if not chunked_text:
        raise ValueError("No chunks produced")
    logger.info("ingest_document: produced %d chunks (doc=%s)", len(chunked_text), doc_id)

    texts = [d.page_content for d in chunked_text]
    embeddings = await embed_batch(client=openai, model=get_settings().EMBEDDING_MODEL, texts=texts)
    logger.info("ingest_document: embedded %d chunks (doc=%s)", len(embeddings), doc_id)

    doc.raw_text = parsed_text
    doc.status = "success"
    session.add_all([Chunk(text=t, embedding=e, document_id=doc.id) for t, e in zip(texts, embeddings)])
    await session.commit()
    logger.info("ingest_document done: doc=%s chunks=%d", doc_id, len(texts))


async def mark_document_failed(doc_id: int, session: AsyncSession) -> None:
    doc = await session.get(DocumentModel, doc_id)
    if doc is None:
        return
    doc.status = "failed"
    await session.commit()
    logger.info("mark_document_failed: doc=%s", doc_id)


async def select_document(id: int, user_id: UUID, session: AsyncSession) -> DocumentModel:
    doc = await session.scalar(select(DocumentModel).where(DocumentModel.id == id, DocumentModel.owner_id == user_id))
    if not doc:
        logger.info("select_document: not found (id=%s user=%s)", id, user_id)
        raise HTTPException(404, "Document not found")
    return doc


async def update_document(id: int, user_id: UUID, title: str, session: AsyncSession) -> DocumentModel:
    doc = await select_document(id=id, user_id=user_id, session=session)
    logger.info("update_document: id=%s new_title=%r", id, title)
    doc.title = title
    await session.commit()
    await session.refresh(doc)
    return doc


async def delete_document(id: int, user_id: UUID, session: AsyncSession) -> None:
    doc = await select_document(id=id, user_id=user_id, session=session)
    logger.info("delete_document: id=%s user=%s", id, user_id)
    await session.delete(doc)
    await session.commit()


async def list_document_chunks(
    id: int, user_id: UUID, session: AsyncSession, limit: int, offset: int
) -> list[Chunk]:
    await select_document(id=id, user_id=user_id, session=session)
    result = await session.execute(
        select(Chunk)
        .where(Chunk.document_id == id)
        .order_by(Chunk.id.asc())
        .limit(limit)
        .offset(offset)
    )
    chunks = list(result.scalars().all())
    logger.info("list_document_chunks: id=%s returned=%d", id, len(chunks))
    return chunks
