from rag.generator import build_context
from rag.routes import _replay_pieces, _sse


def test_sse_simple_token():
    assert _sse("hello") == "data: hello\n\n"


def test_sse_newlines_become_multiple_data_lines():
    assert _sse("a\nb") == "data: a\ndata: b\n\n"


def test_sse_roundtrip_matches_frontend_parsing():
    for token in ["a\nb", " leading", "trail\n", "\n\n", "x"]:
        block = _sse(token)[:-2]  # strip event terminator
        lines = [l for l in block.split("\n") if l.startswith("data:")]
        decoded = "\n".join(l[6:] if l.startswith("data: ") else l[5:] for l in lines)
        assert decoded == token


def test_replay_pieces_reassemble_exactly():
    text = "Hello  world\n\nthis is   a test "
    assert "".join(_replay_pieces(text)) == text


def test_build_context_respects_limit_and_labels_sources():
    chunks = [
        {"text": "x" * 5000, "metadata": {"filename": "a.pdf", "page_number": 2}},
        {"text": "y" * 5000, "metadata": {"filename": "b.pdf", "page_number": 1}},
        {"text": "z" * 5000, "metadata": {"filename": "c.pdf", "page_number": 1}},
    ]
    context = build_context(chunks, max_chars=12000)
    assert len(context) <= 12000
    assert context.startswith("[a.pdf, page 2]")
