from rag.retriever import reciprocal_rank_fusion


def item(i: str) -> dict:
    return {"id": i, "text": i, "metadata": {}}


def test_item_in_both_lists_ranks_first():
    vector = [item("a"), item("b"), item("c")]
    keyword = [item("c"), item("d")]
    merged = reciprocal_rank_fusion([vector, keyword])
    assert merged[0]["id"] == "c"  # 1/63 + 1/61 beats a's 1/61
    ids = [m["id"] for m in merged]
    assert set(ids) == {"a", "b", "c", "d"}
    assert len(ids) == len(set(ids))


def test_scores_use_k_60():
    merged = reciprocal_rank_fusion([[item("a")], [item("a")]])
    assert merged[0]["rrf_score"] == 2 / 61


def test_empty_inputs():
    assert reciprocal_rank_fusion([[], []]) == []
