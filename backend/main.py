"""FastAPI application entrypoint: app factory, CORS and lifespan."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from config import settings
from auth import models as auth_models  # noqa: F401  (register tables on Base.metadata)
from auth.routes import router as auth_router
from database import close_db, engine, init_db
from chat_history import models as chat_models  # noqa: F401
from documents import models as document_models  # noqa: F401
from documents.routes import router as documents_router
from rag.routes import router as chat_router

logger = logging.getLogger("ai_doc_assistant")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Create DB tables on startup and release resources on shutdown."""
    try:
        await init_db()
        logger.info("Database initialised")
    except Exception:  # noqa: BLE001 - keep the API up so /health reports the problem
        logger.exception("Database initialisation failed - check DATABASE_URL and that MySQL is running")
    yield
    await close_db()


app = FastAPI(title="AI Document Assistant", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Session-Id"],
)


app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(chat_router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Report API and database status."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db = "ok"
    except Exception as exc:  # noqa: BLE001
        db = f"error: {type(exc).__name__}"
    return {"status": "ok", "database": db}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=settings.app_host, port=settings.app_port, reload=True)
