"""Pluggable RAG manager with an optional FAISS backend and an in-memory fallback.

This module provides a small RAGManager class you can instantiate with an
embedder callable (text -> vector) and a storage directory. If FAISS is
available it will be used; otherwise an in-memory numpy-backed index will be
used for development and tests.
"""
from __future__ import annotations

import os
import threading
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

try:
    from .backends import faiss_backend
    FAISS_AVAILABLE = True
except Exception:
    faiss_backend = None  # type: ignore
    FAISS_AVAILABLE = False

import numpy as np


class RAGManager:
    """Manage documents and perform semantic search.

    Args:
        embedder: callable(texts: Iterable[str]) -> List[List[float]] or np.ndarray
        storage_dir: directory where local chroma or persisted artifacts live
        collection_name: name for vector collection
    """

    def __init__(self, embedder: Callable[[Iterable[str]], List[List[float]]], storage_dir: Optional[str] = None, collection_name: str = "crew_rag"):
        self.embedder = embedder
        self.storage_dir = storage_dir or os.getcwd()
        self.collection_name = collection_name
        self._lock = threading.Lock()

        # Prefer FAISS if available, else memory
        if FAISS_AVAILABLE and faiss_backend is not None:
            try:
                self._client = faiss_backend.client(self.storage_dir)
                self._col = faiss_backend.get_or_create_collection(self._client, self.collection_name)
                self._backend = "faiss"
            except Exception:
                self._client = None
                self._col = None
                self._backend = "memory"
        else:
            self._client = None
            self._col = None
            self._backend = "memory"

        # In-memory store: lists of ids, texts, metas and vectors
        self._ids: List[str] = []
        self._texts: List[str] = []
        self._metas: List[Dict[str, Any]] = []
        self._vecs: Optional[np.ndarray] = None

    def add_documents(self, docs: Iterable[Tuple[str, str, Optional[Dict[str, Any]]]]):
        """Add documents.

        Each doc is (id, text, metadata).
        """
        docs_list = list(docs)
        if not docs_list:
            return

        ids, texts, metas = zip(*docs_list)
        vectors = np.array(self.embedder(texts), dtype=float)

        with self._lock:
            if self._backend == "faiss" and self._col is not None and faiss_backend is not None:
                faiss_backend.add(self._col, ids, texts, vectors.tolist(), metas)
            else:
                # memory append
                self._ids.extend(ids)
                self._texts.extend(texts)
                self._metas.extend(metas)
                if self._vecs is None:
                    self._vecs = vectors
                else:
                    self._vecs = np.vstack([self._vecs, vectors])

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Return top-k documents for the query.

        Returns list of dicts: {id, text, metadata, score}
        """
        qvec = np.array(self.embedder([query]), dtype=float)[0]

        with self._lock:
            if self._backend == "faiss" and self._col is not None and faiss_backend is not None:
                return faiss_backend.query(self._col, qvec.tolist(), k)
            else:
                if self._vecs is None or len(self._ids) == 0:
                    return []
                # cosine similarity
                vecs = self._vecs
                norms = np.linalg.norm(vecs, axis=1) * (np.linalg.norm(qvec) + 1e-12)
                sims = (vecs @ qvec) / norms
                idx = np.argsort(-sims)[:k]
                results = []
                for i in idx:
                    results.append({"id": self._ids[int(i)], "text": self._texts[int(i)], "metadata": self._metas[int(i)], "score": float(sims[int(i)])})
                return results

    def persist(self):
        """Persist backend state (no-op for memory)."""
        if self._backend == "faiss" and self._client is not None and faiss_backend is not None:
            faiss_backend.persist(self._client)

    def clear(self):
        with self._lock:
            if self._backend == "faiss" and self._col is not None and faiss_backend is not None:
                faiss_backend.delete_collection(self._client, self.collection_name)
                self._client = faiss_backend.client(self.storage_dir)
                self._col = faiss_backend.get_or_create_collection(self._client, self.collection_name)
            else:
                self._ids = []
                self._texts = []
                self._metas = []
                self._vecs = None


__all__ = ["RAGManager"]
