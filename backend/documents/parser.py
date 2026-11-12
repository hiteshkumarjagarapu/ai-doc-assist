"""Extract text from PDF, DOCX and PPTX files."""

import asyncio
import io
from pathlib import PurePath

from docx import Document as DocxDocument
from pptx import Presentation
from pypdf import PdfReader

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".pptx"}

# A parsed document is a list of (page_number, text); page numbers start at 1.
Pages = list[tuple[int, str]]


def _parse_pdf(data: bytes) -> Pages:
    """Extract text page by page from a PDF."""
    reader = PdfReader(io.BytesIO(data))
    return [(i, page.extract_text() or "") for i, page in enumerate(reader.pages, start=1)]


def _parse_docx(data: bytes) -> Pages:
    """Extract paragraphs (and table cell text) from a Word document as a single page."""
    doc = DocxDocument(io.BytesIO(data))
    parts = [p.text for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            parts.extend(c.text for c in row.cells if c.text.strip())
    return [(1, "\n".join(parts))]


def _parse_pptx(data: bytes) -> Pages:
    """Extract text from each slide; the slide number is used as the page number."""
    prs = Presentation(io.BytesIO(data))
    pages: Pages = []
    for i, slide in enumerate(prs.slides, start=1):
        texts = [
            shape.text_frame.text
            for shape in slide.shapes
            if shape.has_text_frame and shape.text_frame.text.strip()
        ]
        pages.append((i, "\n".join(texts)))
    return pages


def parse_document_sync(filename: str, data: bytes) -> Pages:
    """Parse a document by extension. Raises ValueError for unsupported or unreadable files."""
    ext = PurePath(filename).suffix.lower()
    parsers = {".pdf": _parse_pdf, ".docx": _parse_docx, ".pptx": _parse_pptx}
    if ext not in parsers:
        raise ValueError(f"Unsupported file type '{ext}'. Allowed: PDF, DOCX, PPTX")
    try:
        return parsers[ext](data)
    except Exception as exc:  # noqa: BLE001 - library errors vary; surface as unreadable
        raise ValueError(f"Could not read file: {exc}") from exc


async def parse_document(filename: str, data: bytes) -> Pages:
    """Parse a document in a worker thread so the event loop is not blocked."""
    return await asyncio.to_thread(parse_document_sync, filename, data)
