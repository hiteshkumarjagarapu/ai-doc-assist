import io

import pytest
from docx import Document

from documents.parser import parse_document_sync


def test_docx_text_extracted():
    doc = Document()
    doc.add_paragraph("First paragraph")
    doc.add_paragraph("Second paragraph")
    buf = io.BytesIO()
    doc.save(buf)
    pages = parse_document_sync("notes.docx", buf.getvalue())
    assert pages == [(1, "First paragraph\nSecond paragraph")]


def test_unsupported_extension_rejected():
    with pytest.raises(ValueError, match="Unsupported"):
        parse_document_sync("notes.txt", b"hi")


def test_corrupt_file_rejected():
    with pytest.raises(ValueError, match="Could not read"):
        parse_document_sync("broken.pdf", b"not a pdf")
