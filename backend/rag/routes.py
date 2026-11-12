"""Chat routes: streaming RAG answer, history and session list.

SSE format: each token is sent as ``data: <token>\\n\\n``. A token containing newlines is
split into several ``data:`` lines (standard SSE; clients rejoin them with "\\n").
The stream ends with ``data: [DONE]\\n\\n``. The session id is returned in the
``X-Session-Id`` response header.
"""

import logging
import re
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user
from auth.models import User
from chat_history import service as history
from database import AsyncSessionLocal, get_db
from rag import cache
from rag.generator import build_context, generator
from rag.reranker import get_reranker
from rag.retriever import get_retriever
from rag.schemas import ChatHistoryResponse, ChatRequest, MessageOut, SessionOut

logger = logging.getLogger("ai_doc_assistant.chat")

router = APIRouter(prefix="/chat", tags=["chat"])

NO_DOCS_MESSAGE = "I couldn't find any relevant information in your uploaded documents."


def _sse(token: str) -> str:
    """Format a token as an SSE event, splitting embedded newlines into data lines."""
    return "".join(f"data: {line}\n" for line in token.split("\n")) + "\n"


def _replay_pieces(text: str) -> list[str]:
    """Split a cached answer into word-sized pieces so it streams like a live answer."""
    return re.findall(r"\S+\s*|\s+", text)


async def _answer_stream(query: str, user_id: int, session_id: str) -> AsyncIterator[str]:
    """Produce SSE events for a query, then cache and persist the full answer."""
    answer_parts: list[str] = []
    try:
        cached = await cache.get_cached(query, user_id)
        if cached is not None:
            for piece in _replay_pieces(cached):
                answer_parts.append(piece)
                yield _sse(piece)
        else:
            candidates = await get_retriever().retrieve(query, user_id)
            top = await get_reranker().rerank(query, candidates, top_n=5)
            if not top:
                answer_parts.append(NO_DOCS_MESSAGE)
                yield _sse(NO_DOCS_MESSAGE)
            else:
                context = build_context(top)
                async for token in generator.stream_answer(query, context):
                    answer_parts.append(token)
                    yield _sse(token)
                await cache.set_cached(query, user_id, "".join(answer_parts))
    except Exception:  # noqa: BLE001 - report to the client instead of dropping the stream
        logger.exception("Chat stream failed")
        yield _sse("[ERROR] Failed to generate an answer. Please try again.")
        yield "data: [DONE]\n\n"
        return

    yield "data: [DONE]\n\n"

    try:
        async with AsyncSessionLocal() as db:
            await history.save_exchange(db, session_id, query, "".join(answer_parts))
    except SQLAlchemyError:
        logger.exception("Failed to save chat history")


@router.post("")
async def chat(
    body: ChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Answer a question about the user's documents as a text/event-stream."""
    query = body.query.strip()
    if not query:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Query must not be empty")
    user_id = user.id
    try:
        if body.session_id:
            session = await history.get_session(db, body.session_id)
            if session is None or session.user_id != user_id:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
            session_id = session.id
        else:
            session_id = str(uuid.uuid4())
            await history.create_session(db, session_id, user_id, query)
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Database error") from None

    return StreamingResponse(
        _answer_stream(query, user_id, session_id),
        media_type="text/event-stream",
        headers={"X-Session-Id": session_id, "Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/sessions", response_model=list[SessionOut])
async def list_sessions(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """List the user's chat sessions, newest first."""
    return await history.list_sessions(db, user.id)


@router.get("/history/{session_id}", response_model=ChatHistoryResponse)
async def chat_history(
    session_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> ChatHistoryResponse:
    """Return the messages of one of the user's sessions."""
    session = await history.get_session(db, session_id)
    if session is None or session.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    messages = await history.get_messages(db, session_id)
    return ChatHistoryResponse(
        session_id=session_id,
        messages=[
            MessageOut(role=m.role, content=m.content, timestamp=m.created_at.isoformat())  # type: ignore[arg-type]
            for m in messages
        ],
    )
