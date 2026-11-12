"""Split parsed pages into overlapping chunks with metadata."""

from typing import Any, TypedDict

from langchain_text_splitters import RecursiveCharacterTextSplitter

from documents.parser import Pages

CHUNK_SIZE = 500
CHUNK_OVERLAP = 80


class Chunk(TypedDict):
    """A text chunk and its metadata."""

    text: str
    metadata: dict[str, Any]


_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)


def chunk_pages(pages: Pages, doc_id: int, filename: str, user_id: int) -> list[Chunk]:
    """Chunk each page; metadata: {doc_id, filename, page_number, chunk_index, user_id}."""
    chunks: list[Chunk] = []
    for page_number, text in pages:
        if not text.strip():
            continue
        for piece in _splitter.split_text(text):
            chunks.append(
                {
                    "text": piece,
                    "metadata": {
                        "doc_id": doc_id,
                        "filename": filename,
                        "page_number": page_number,
                        "chunk_index": len(chunks),
                        "user_id": user_id,
                    },
                }
            )
    return chunks
