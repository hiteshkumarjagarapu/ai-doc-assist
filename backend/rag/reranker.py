"""CrossEncoder reranking of retrieved candidates."""

import asyncio
from functools import lru_cache
from typing import Any

from sentence_transformers import CrossEncoder

MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class Reranker:
    """Lazy-loading wrapper around a CrossEncoder model."""

    def __init__(self, model_name: str = MODEL_NAME) -> None:
        self._model_name = model_name
        self._model: CrossEncoder | None = None

    def _rerank_sync(self, query: str, candidates: list[dict[str, Any]], top_n: int) -> list[dict[str, Any]]:
        """Score (query, chunk) pairs and return the best top_n (blocking)."""
        if self._model is None:
            self._model = CrossEncoder(self._model_name)
        scores = self._model.predict([(query, c["text"]) for c in candidates])
        ranked = sorted(zip(candidates, scores), key=lambda p: float(p[1]), reverse=True)
        return [{**c, "rerank_score": float(s)} for c, s in ranked[:top_n]]

    async def rerank(self, query: str, candidates: list[dict[str, Any]], top_n: int = 5) -> list[dict[str, Any]]:
        """Return the top_n candidates ordered by cross-encoder relevance, off the event loop."""
        if not candidates:
            return []
        return await asyncio.to_thread(self._rerank_sync, query, candidates, top_n)


@lru_cache
def get_reranker() -> Reranker:
    """Return the shared Reranker instance."""
    return Reranker()
