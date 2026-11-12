"""Hybrid retrieval: vector search + BM25 merged with Reciprocal Rank Fusion."""

import asyncio
from typing import Any

from rag import bm25_search, vector_store
from rag.embeddings import EmbeddingService, get_embedding_service

RRF_K = 60


def reciprocal_rank_fusion(
    result_lists: list[list[dict[str, Any]]], k: int = RRF_K
) -> list[dict[str, Any]]:
    """Merge ranked result lists by id: score = sum(1 / (k + rank)), rank starting at 1.

    Returns merged results sorted by descending ``rrf_score``.
    """
    scores: dict[str, float] = {}
    items: dict[str, dict[str, Any]] = {}
    for results in result_lists:
        for rank, item in enumerate(results, start=1):
            scores[item["id"]] = scores.get(item["id"], 0.0) + 1.0 / (k + rank)
            items.setdefault(item["id"], item)
    ordered = sorted(scores, key=lambda i: scores[i], reverse=True)
    return [{**items[i], "rrf_score": scores[i]} for i in ordered]


class HybridRetriever:
    """Combines ChromaDB vector search and BM25 keyword search."""

    def __init__(self, embedder: EmbeddingService | None = None, top_k: int = 10) -> None:
        self._embedder = embedder or get_embedding_service()
        self._top_k = top_k

    async def retrieve(self, query: str, user_id: int, limit: int | None = None) -> list[dict[str, Any]]:
        """Return merged candidates for a user's query (vector top-k + BM25 top-k, RRF k=60)."""
        embedding = await self._embedder.embed_query(query)
        vector_results, keyword_results = await asyncio.gather(
            vector_store.search(embedding, user_id, self._top_k),
            bm25_search.search(query, user_id, self._top_k),
        )
        merged = reciprocal_rank_fusion([vector_results, keyword_results])
        return merged[:limit] if limit else merged


def get_retriever() -> HybridRetriever:
    """Return a HybridRetriever using the shared embedding service."""
    return HybridRetriever()
