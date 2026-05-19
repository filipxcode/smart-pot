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


async def rag_upload(title: str, data: bytes, user_id: UUID, session: AsyncSession, openai: AsyncOpenAI) -> DocumentModel:
    logger.info("rag_upload start: title=%r size=%d user=%s", title, len(data), user_id)

    parsed_text = parse_pdf(data)
    if not parsed_text:
        logger.warning("rag_upload: empty PDF (user=%s title=%r)", user_id, title)
        raise HTTPException(422, "Empty or unreadable PDF")
    logger.info("rag_upload: parsed %d chars", len(parsed_text))

    chunked_text = chunk_text(parsed_text)
    if not chunked_text:
        logger.warning("rag_upload: no chunks (user=%s title=%r)", user_id, title)
        raise HTTPException(422, "No chunks produced")
    logger.info("rag_upload: produced %d chunks", len(chunked_text))

    texts = [d.page_content for d in chunked_text]
    embeddings = await embed_batch(client=openai, model=get_settings().EMBEDDING_MODEL, texts=texts)
    logger.info("rag_upload: embedded %d chunks", len(embeddings))

    doc = DocumentModel(title=title, raw_text=parsed_text, owner_id=user_id)
    doc.chunks = [Chunk(text=t, embedding=e) for t, e in zip(texts, embeddings)]
    session.add(doc)
    await session.commit()
    await session.refresh(doc)
    logger.info("rag_upload done: document_id=%s chunks=%d", doc.id, len(doc.chunks))
    return doc


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