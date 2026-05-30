import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status, BackgroundTasks
from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import current_active_user
from api.db import async_session_maker, get_async_session
from api.dependencies import get_openai_client
from api.models.document import DocumentModel
from api.models.user import User
from api.service.document import (
    create_pending_document,
    delete_document,
    ingest_document,
    list_document_chunks,
    mark_document_failed,
    select_document,
    update_document,
)
from api.schemas.document import ChunkRead, DocumentRawRead, DocumentRead, DocumentUpdate

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 10 * 1024 * 1024
READ_CHUNK_SIZE = 1024 * 1024
PDF_MAGIC_BYTES = b"%PDF-"

router = APIRouter(prefix="/file", tags=["file"])

async def proceed_file(doc_id: int, data: bytes, openai: AsyncOpenAI) -> None:
    # Runs AFTER the response is sent: own session, no request-scoped objects.
    async with async_session_maker() as session:
        try:
            await ingest_document(doc_id=doc_id, data=data, session=session, openai=openai)
        except Exception:
            logger.exception("Ingest failed: doc=%s", doc_id)
            await session.rollback()
            await mark_document_failed(doc_id=doc_id, session=session)


@router.post("", response_model=DocumentRead, status_code=status.HTTP_202_ACCEPTED)
async def upload_file(
    background_tasks: BackgroundTasks,
    title: str = Form(..., min_length=1, max_length=100),
    file: UploadFile = File(...),
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
    openai: AsyncOpenAI = Depends(get_openai_client),
) -> DocumentModel:
    """Validate the file in-request, create a pending document, then ingest it in the background."""
    if file.content_type != "application/pdf":
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Unsupported file type")

    # Read/validate the file IN the request — UploadFile is closed once we respond.
    chunks: list[bytes] = []
    total = 0
    while chunk := await file.read(READ_CHUNK_SIZE):
        total += len(chunk)
        if total > MAX_FILE_SIZE:
            raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File too large")
        chunks.append(chunk)
    data = b"".join(chunks)

    if not data.startswith(PDF_MAGIC_BYTES):
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "File is not a valid PDF")

    doc = await create_pending_document(title=title, user_id=user.id, session=session)
    logger.info("Upload accepted: doc=%s user=%s title=%r size=%d", doc.id, user.id, title, total)
    background_tasks.add_task(proceed_file, doc.id, data, openai)
    return doc

@router.get("", response_model=list[DocumentRead])
async def read_documents(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(
        select(DocumentModel)
        .where(DocumentModel.owner_id == user.id)
        .order_by(DocumentModel.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()

@router.get("/{doc_id}", response_model=DocumentRead)
async def read_document(doc_id: int, user: User = Depends(current_active_user), session: AsyncSession = Depends(get_async_session)):
    return await select_document(id=doc_id, user_id=user.id, session=session)


@router.patch("/{doc_id}", response_model=DocumentRead)
async def patch_document(
    doc_id: int,
    body: DocumentUpdate,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    return await update_document(id=doc_id, user_id=user.id, title=body.title, session=session)


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_document(
    doc_id: int,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    await delete_document(id=doc_id, user_id=user.id, session=session)


@router.get("/{doc_id}/raw", response_model=DocumentRawRead)
async def read_document_raw(
    doc_id: int,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    return await select_document(id=doc_id, user_id=user.id, session=session)


@router.get("/{doc_id}/chunks", response_model=list[ChunkRead])
async def read_document_chunks(
    doc_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    return await list_document_chunks(
        id=doc_id, user_id=user.id, session=session, limit=limit, offset=offset
    )
