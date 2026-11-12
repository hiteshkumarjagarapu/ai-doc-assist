"""BM25 keyword search over a persisted, per-user chunk corpus."""

import asyncio
import json
import re
import threading
from pathlib import Path
from typing import Any

from rank_bm25 import BM25Okapi

from config import settings
from documents.chunker import Chunk

_TOKEN_RE = re.compile(r"\w+")


def _tokenize(text: str) -> list[str]:
    """Lowercase and split text into word tokens."""
    return _TOKEN_RE.findall(text.lower())


class BM25Store:
    """Thread-safe BM25 corpus persisted to a JSON file; indexes are built lazily per user."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = threading.Lock()
        self._chunks: list[Chunk] = []
        self._indexes: dict[int, tuple[list[Chunk], list[list[str]], BM25Okapi]] = {}
        self._load()

    def _load(self) -> None:
        """Load the corpus from disk if present."""
        if self._path.exists():
            try:
                self._chunks = json.loads(self._path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._chunks = []

    def _save(self) -> None:
        """Persist the corpus atomically."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._chunks), encoding="utf-8")
        tmp.replace(self._path)

    def add(self, chunks: list[Chunk]) -> None:
        """Add chunks to the corpus and persist."""
        with self._lock:
            self._chunks.extend(chunks)
            for chunk in chunks:
                self._indexes.pop(chunk["metadata"]["user_id"], None)
            self._save()

    def delete_document(self, doc_id: int) -> None:
        """Remove all chunks of a document and persist."""
        with self._lock:
            removed = [c for c in self._chunks if c["metadata"]["doc_id"] == doc_id]
            if not removed:
                return
            self._chunks = [c for c in self._chunks if c["metadata"]["doc_id"] != doc_id]
            self._indexes.pop(removed[0]["metadata"]["user_id"], None)
            self._save()

    def search(self, query: str, user_id: int, n_results: int) -> list[dict[str, Any]]:
        """Return the top chunks for a user that share at least one term with the query."""
        q_tokens = _tokenize(query)
        if not q_tokens:
            return []
        with self._lock:
            if user_id not in self._indexes:
                user_chunks = [c for c in self._chunks if c["metadata"]["user_id"] == user_id]
                if not user_chunks:
                    return []
                tokens = [_tokenize(c["text"]) for c in user_chunks]
                self._indexes[user_id] = (user_chunks, tokens, BM25Okapi(tokens))
            user_chunks, tokens, bm25 = self._indexes[user_id]
            scores = bm25.get_scores(q_tokens)
        q_set = set(q_tokens)
        ranked = sorted(range(len(user_chunks)), key=lambda i: scores[i], reverse=True)
        results: list[dict[str, Any]] = []
        for i in ranked:
            if not q_set.intersection(tokens[i]):
                continue  # BM25 scores can be <= 0 on tiny corpora; require real term overlap
            meta = user_chunks[i]["metadata"]
            results.append(
                {
                    "id": f"{meta['doc_id']}_{meta['chunk_index']}",
                    "text": user_chunks[i]["text"],
                    "metadata": meta,
                    "score": float(scores[i]),
                }
            )
            if len(results) >= n_results:
                break
        return results


_store: BM25Store | None = None
_store_lock = threading.Lock()


def get_store() -> BM25Store:
    """Return the shared BM25Store."""
    global _store
    with _store_lock:
        if _store is None:
            _store = BM25Store(Path(settings.chroma_dir) / "bm25_corpus.json")
        return _store


async def add_chunks(chunks: list[Chunk]) -> None:
    """Add chunks to the BM25 corpus."""
    if chunks:
        await asyncio.to_thread(get_store().add, chunks)


async def search(query: str, user_id: int, n_results: int = 10) -> list[dict[str, Any]]:
    """Keyword search over a user's chunks; returns [{id, text, metadata, score}]."""
    return await asyncio.to_thread(get_store().search, query, user_id, n_results)


async def delete_document(doc_id: int) -> None:
    """Remove a document's chunks from the BM25 corpus."""
    await asyncio.to_thread(get_store().delete_document, doc_id)
