"""Document routes: upload, list, delete."""

from pathlib import PurePath

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user
from auth.models import User
from config import settings
from database import get_db
from documents.chunker import chunk_pages
from documents.models import Document
from documents.parser import SUPPORTED_EXTENSIONS, parse_document
from documents.schemas import DocumentResponse, UploadResponse
from rag import bm25_search, cache, vector_store
from rag.embeddings import get_embedding_service

router = APIRouter(prefix="/docs", tags=["documents"])


async def _remove_index(doc_id: int) -> None:
    """Remove a document's chunks from ChromaDB and the BM25 corpus."""
    await vector_store.delete_document(doc_id)
    await bm25_search.delete_document(doc_id)


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UploadResponse:
    """Upload a PDF/DOCX/PPTX (max 10MB), parse and chunk it, and save its record."""
    filename = PurePath(file.filename or "").name
    if PurePath(filename).suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Only PDF, DOCX and PPTX files are allowed")

    max_bytes = settings.max_upload_mb * 1024 * 1024
    data = await file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, f"File exceeds {settings.max_upload_mb}MB limit")
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "File is empty")

    try:
        pages = await parse_document(filename, data)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from None

    try:
        doc = Document(filename=filename, user_id=user.id, chunk_count=0)
        db.add(doc)
        await db.flush()  # assigns doc.id for chunk metadata
        chunks = chunk_pages(pages, doc.id, filename, user.id)
        if not chunks:
            await db.rollback()
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "No extractable text found in document")
        doc.chunk_count = len(chunks)
        embeddings = await get_embedding_service().embed_documents([c["text"] for c in chunks])
        await vector_store.add_chunks(chunks, embeddings)
        await bm25_search.add_chunks(chunks)
        await db.commit()
        await db.refresh(doc)
    except HTTPException:
        raise
    except SQLAlchemyError:
        await db.rollback()
        await _remove_index(doc.id)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Database error") from None
    except Exception:  # noqa: BLE001 - embedding / vector store failure
        await db.rollback()
        await _remove_index(doc.id)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to index document") from None

    return UploadResponse(message="Document uploaded", document=DocumentResponse.model_validate(doc))


@router.get("/list", response_model=list[DocumentResponse])
async def list_documents(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[Document]:
    """Return the current user's documents, newest first."""
    result = await db.scalars(
        select(Document).where(Document.user_id == user.id).order_by(Document.created_at.desc(), Document.id.desc())
    )
    return list(result)


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> None:
    """Delete one of the user's documents."""
    doc = await db.scalar(select(Document).where(Document.id == doc_id, Document.user_id == user.id))
    if doc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    try:
        await _remove_index(doc.id)
        await db.delete(doc)
        await db.commit()
        await cache.clear_user_cache(user.id)
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Database error") from None
