"""Save and fetch chat history."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chat_history.models import ChatMessage, ChatSession


async def get_session(db: AsyncSession, session_id: str) -> ChatSession | None:
    """Return a session by id, or None."""
    return await db.get(ChatSession, session_id)


async def create_session(db: AsyncSession, session_id: str, user_id: int, title: str) -> ChatSession:
    """Create and commit a new session."""
    session = ChatSession(id=session_id, user_id=user_id, title=title[:120])
    db.add(session)
    await db.commit()
    return session


async def save_exchange(db: AsyncSession, session_id: str, query: str, answer: str) -> None:
    """Save a user query and the AI answer to a session."""
    db.add(ChatMessage(session_id=session_id, role="user", content=query))
    db.add(ChatMessage(session_id=session_id, role="ai", content=answer))
    await db.commit()


async def get_messages(db: AsyncSession, session_id: str) -> list[ChatMessage]:
    """Return a session's messages in chronological order."""
    result = await db.scalars(
        select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.id)
    )
    return list(result)


async def list_sessions(db: AsyncSession, user_id: int) -> list[ChatSession]:
    """Return a user's sessions, newest first."""
    result = await db.scalars(
        select(ChatSession).where(ChatSession.user_id == user_id).order_by(ChatSession.created_at.desc())
    )
    return list(result)
