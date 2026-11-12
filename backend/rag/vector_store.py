"""ChromaDB persistent vector store."""

import asyncio
from functools import lru_cache
from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection

from config import settings
from documents.chunker import Chunk

COLLECTION_NAME = "documents"


@lru_cache
def _get_collection() -> Collection:
    """Return the persistent collection (cosine distance), creating it if needed."""
    client = chromadb.PersistentClient(path=settings.chroma_dir)
    return client.get_or_create_collection(COLLECTION_NAME, metadata={"hnsw:space": "cosine"})


def _chunk_id(metadata: dict[str, Any]) -> str:
    """Build a unique chunk id from its metadata."""
    return f"{metadata['doc_id']}_{metadata['chunk_index']}"


def _add_sync(chunks: list[Chunk], embeddings: list[list[float]]) -> None:
    """Insert chunks and their embeddings (blocking)."""
    _get_collection().add(
        ids=[_chunk_id(c["metadata"]) for c in chunks],
        documents=[c["text"] for c in chunks],
        metadatas=[c["metadata"] for c in chunks],
        embeddings=embeddings,
    )


def _search_sync(embedding: list[float], user_id: int, n_results: int) -> list[dict[str, Any]]:
    """Query the collection restricted to one user's chunks (blocking)."""
    res = _get_collection().query(
        query_embeddings=[embedding],
        n_results=n_results,
        where={"user_id": user_id},
        include=["documents", "metadatas", "distances"],
    )
    return [
        {"id": i, "text": t, "metadata": m, "distance": d}
        for i, t, m, d in zip(res["ids"][0], res["documents"][0], res["metadatas"][0], res["distances"][0])
    ]


def _delete_sync(doc_id: int) -> None:
    """Delete all chunks of a document (blocking)."""
    _get_collection().delete(where={"doc_id": doc_id})


async def add_chunks(chunks: list[Chunk], embeddings: list[list[float]]) -> None:
    """Store chunks with their embeddings."""
    if chunks:
        await asyncio.to_thread(_add_sync, chunks, embeddings)


async def search(query_embedding: list[float], user_id: int, n_results: int = 10) -> list[dict[str, Any]]:
    """Vector search over a user's chunks; returns [{id, text, metadata, distance}]."""
    return await asyncio.to_thread(_search_sync, query_embedding, user_id, n_results)


async def delete_document(doc_id: int) -> None:
    """Remove every chunk belonging to a document."""
    await asyncio.to_thread(_delete_sync, doc_id)
