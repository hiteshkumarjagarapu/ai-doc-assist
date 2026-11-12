"""Embedding service using BAAI/bge-small-en (384 dimensions)."""

import asyncio
from functools import lru_cache

from sentence_transformers import SentenceTransformer

MODEL_NAME = "BAAI/bge-small-en"
QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "


class EmbeddingService:
    """Lazy-loading wrapper around a SentenceTransformer model."""

    def __init__(self, model_name: str = MODEL_NAME) -> None:
        self._model_name = model_name
        self._model: SentenceTransformer | None = None

    def _get_model(self) -> SentenceTransformer:
        """Load the model on first use."""
        if self._model is None:
            self._model = SentenceTransformer(self._model_name)
        return self._model

    def _encode(self, texts: list[str]) -> list[list[float]]:
        """Encode texts into normalised vectors (blocking)."""
        vectors = self._get_model().encode(texts, normalize_embeddings=True, batch_size=32)
        return vectors.tolist()

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed document chunks without blocking the event loop."""
        if not texts:
            return []
        return await asyncio.to_thread(self._encode, texts)

    async def embed_query(self, query: str) -> list[float]:
        """Embed a search query (with the BGE retrieval instruction prefix)."""
        vectors = await asyncio.to_thread(self._encode, [QUERY_INSTRUCTION + query])
        return vectors[0]


@lru_cache
def get_embedding_service() -> EmbeddingService:
    """Return the shared EmbeddingService instance."""
    return EmbeddingService()
