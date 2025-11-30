#!/usr/bin/env python3
"""Simple FAISS benchmark using the project's FAISS backend adapter.

Generates synthetic vectors, indexes them, and times queries.
"""
import time
import tempfile
import numpy as np
from crew_ai.backends import faiss_backend


def make_docs(n, dim=128):
    ids = [f"doc{i}" for i in range(n)]
    texts = [f"text {i}" for i in range(n)]
    vecs = np.random.randn(n, dim).astype(float)
    metas = [{} for _ in range(n)]
    return ids, texts, vecs, metas


def bench(n=1000, dim=128, k=10):
    with tempfile.TemporaryDirectory() as td:
        client = faiss_backend.client(td)
        col = faiss_backend.get_or_create_collection(client, "benchcol")
        ids, texts, vecs, metas = make_docs(n, dim)
        print("Indexing...", n)
        t0 = time.time()
        faiss_backend.add(col, ids, texts, vecs.tolist(), metas)
        t1 = time.time()
        print(f"Indexed {n} docs in {t1-t0:.3f}s")

        q = np.random.randn(dim).astype(float).tolist()
        t0 = time.time()
        hits = faiss_backend.query(col, q, k)
        t1 = time.time()
        print(f"Query returned {len(hits)} results in {t1-t0:.4f}s")
        for h in hits[:5]:
            print(h)


if __name__ == "__main__":
    bench(1000, 128, 10)
