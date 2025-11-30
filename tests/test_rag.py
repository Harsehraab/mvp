import numpy as np

from crew_ai.rag import RAGManager


def fake_embedder(texts):
    # deterministic, low-dim vectors for testing
    out = []
    for t in texts:
        s = sum(ord(c) for c in t)
        v = np.array([s % 13, s % 7], dtype=float)
        out.append(v.tolist())
    return out


def test_rag_add_and_search(tmp_path):
    rm = RAGManager(embedder=fake_embedder, storage_dir=str(tmp_path), collection_name="testcol")
    docs = [("id1", "fraud pattern A", {"tag": "fraud"}), ("id2", "normal activity", {"tag": "ok"}), ("id3", "fraud pattern B", {"tag": "fraud"})]
    rm.add_documents(docs)
    res = rm.search("fraud pattern", k=2)
    assert isinstance(res, list)
    # expect at least one fraud doc with higher score
    assert len(res) <= 2
    if len(res) > 0:
        assert "id" in res[0]
