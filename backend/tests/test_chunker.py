from documents.chunker import CHUNK_SIZE, chunk_pages


def test_metadata_and_sequential_index():
    pages = [(1, "word " * 400), (2, ""), (3, "short text")]
    chunks = chunk_pages(pages, doc_id=7, filename="f.pdf", user_id=3)
    assert chunks
    assert [c["metadata"]["chunk_index"] for c in chunks] == list(range(len(chunks)))
    for c in chunks:
        assert len(c["text"]) <= CHUNK_SIZE
        assert c["metadata"]["doc_id"] == 7
        assert c["metadata"]["filename"] == "f.pdf"
        assert c["metadata"]["user_id"] == 3
    assert {c["metadata"]["page_number"] for c in chunks} == {1, 3}  # blank page skipped


def test_blank_document_has_no_chunks():
    assert chunk_pages([(1, "   \n")], 1, "x.pdf", 1) == []
