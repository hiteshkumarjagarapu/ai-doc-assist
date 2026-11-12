"""Streaming answer generation with the Groq API."""

from collections.abc import AsyncIterator
from typing import Any

from groq import AsyncGroq

from config import settings

SYSTEM_PROMPT = (
    "You are a helpful document assistant. Answer ONLY from provided context. "
    "If answer not in context, say so. Be concise."
)
MAX_CONTEXT_CHARS = 12000


def build_context(chunks: list[dict[str, Any]], max_chars: int = MAX_CONTEXT_CHARS) -> str:
    """Join chunk texts (labelled with source) into one context string, capped at max_chars."""
    parts: list[str] = []
    total = 0
    for chunk in chunks:
        meta = chunk["metadata"]
        part = f"[{meta['filename']}, page {meta['page_number']}]\n{chunk['text']}"
        if total + len(part) > max_chars:
            remaining = max_chars - total
            if remaining > 200:
                parts.append(part[:remaining])
            break
        parts.append(part)
        total += len(part) + 2  # account for the "\n\n" separator
    return "\n\n".join(parts)


class Generator:
    """Streams LLM answers from Groq."""

    def __init__(self) -> None:
        self._client: AsyncGroq | None = None

    def _get_client(self) -> AsyncGroq:
        """Create the Groq client on first use."""
        if self._client is None:
            if not settings.groq_api_key:
                raise RuntimeError("GROQ_API_KEY is not configured")
            self._client = AsyncGroq(api_key=settings.groq_api_key)
        return self._client

    async def stream_answer(self, query: str, context: str) -> AsyncIterator[str]:
        """Yield answer tokens for a query given retrieved context."""
        stream = await self._get_client().chat.completions.create(
            model=settings.groq_model,
            temperature=0.1,
            stream=True,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
            ],
        )
        async for event in stream:
            token = event.choices[0].delta.content if event.choices else None
            if token:
                yield token


generator = Generator()
