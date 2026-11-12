from rag.bm25_search import BM25Store


def make(doc_id: int, user_id: int, idx: int, text: str) -> dict:
    return {
        "text": text,
        "metadata": {
            "doc_id": doc_id, "filename": "f.pdf", "page_number": 1, "chunk_index": idx, "user_id": user_id,
        },
    }


def test_search_ranks_matching_chunk_and_isolates_users(tmp_path):
    store = BM25Store(tmp_path / "bm25.json")
    store.add([
        make(1, 1, 0, "the capital of France is Paris"),
        make(1, 1, 1, "bananas are yellow fruit"),
        make(2, 2, 0, "Paris is also mentioned in another user's file"),
    ])
    results = store.search("capital of France", user_id=1, n_results=5)
    assert results[0]["id"] == "1_0"
    assert all(r["metadata"]["user_id"] == 1 for r in results)


def test_single_chunk_corpus_still_matches(tmp_path):
    store = BM25Store(tmp_path / "bm25.json")
    store.add([make(1, 1, 0, "unique zebra content")])
    assert [r["id"] for r in store.search("zebra", 1, 5)] == ["1_0"]


def test_no_overlap_returns_nothing(tmp_path):
    store = BM25Store(tmp_path / "bm25.json")
    store.add([make(1, 1, 0, "hello world")])
    assert store.search("quantum", 1, 5) == []


def test_delete_and_persistence(tmp_path):
    path = tmp_path / "bm25.json"
    store = BM25Store(path)
    store.add([make(1, 1, 0, "alpha beta"), make(2, 1, 0, "gamma delta")])
    assert BM25Store(path).search("alpha", 1, 5)  # reloaded from disk
    store.delete_document(1)
    assert store.search("alpha", 1, 5) == []
    assert BM25Store(path).search("alpha", 1, 5) == []
    assert store.search("gamma", 1, 5)
