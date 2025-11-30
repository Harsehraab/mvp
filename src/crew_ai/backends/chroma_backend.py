"""ChromaDB backend adapter for the RAG manager.

This adapter tries to import chromadb and exposes a tiny surface that the
RAGManager expects. If chromadb isn't installed, functions raise ImportError.
"""
from __future__ import annotations

import os
from typing import Any, Dict, Iterable, List, Optional

try:
    import chromadb  # type: ignore
    from chromadb.config import Settings  # type: ignore
    CHROMA_AVAILABLE = True
except Exception:
    CHROMA_AVAILABLE = False


def client(storage_dir: Optional[str] = None):
    if not CHROMA_AVAILABLE:
        raise ImportError("chromadb is not installed")
    persist_directory = storage_dir or os.getcwd()
    client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory=persist_directory))
    return client


def get_or_create_collection(client: Any, name: str):
    if not CHROMA_AVAILABLE:
        raise ImportError("chromadb is not installed")
    try:
        return client.get_collection(name)
    except Exception:
        return client.create_collection(name)


def add(col: Any, ids: Iterable[str], texts: Iterable[str], embeddings: List[List[float]], metadatas: Iterable[Dict[str, Any]]):
    col.add(ids=list(ids), documents=list(texts), embeddings=embeddings, metadatas=list(metadatas))


def query(col: Any, embedding: List[float], k: int = 5):
    res = col.query(query_embeddings=[embedding], n_results=k)
    results = []
    for ids, docs, scores, metas in zip(res.get("ids", []), res.get("documents", []), res.get("distances", []), res.get("metadatas", [])):
        for i in range(len(ids)):
            results.append({"id": ids[i], "text": docs[i], "metadata": metas[i], "score": float(scores[i])})
    return results


def persist(client: Any):
    try:
        client.persist()
    except Exception:
        pass


def delete_collection(client: Any, name: str):
    try:
        client.delete_collection(name)
    except Exception:
        pass


__all__ = ["client", "get_or_create_collection", "add", "query", "persist", "delete_collection"]
