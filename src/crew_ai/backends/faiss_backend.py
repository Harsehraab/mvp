"""FAISS backend adapter for the RAG manager.

This adapter provides a simple filesystem-backed FAISS index per collection plus
an id->metadata mapping stored as JSON/NPY files. It's intentionally minimal and
designed for single-process use. For production, run FAISS behind a service.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, Iterable, List, Optional

try:
    import faiss  # type: ignore
    FAISS_AVAILABLE = True
except Exception:
    FAISS_AVAILABLE = False

import numpy as np


def _paths_for(storage_dir: str, collection: str):
    base = os.path.join(storage_dir, collection)
    return {
        "index": base + ".index",
        "ids": base + ".ids.npy",
        "texts": base + ".texts.json",
        "metas": base + ".metas.json",
    }


def client(storage_dir: Optional[str] = None):
    if not FAISS_AVAILABLE:
        raise ImportError("faiss is not installed")
    storage_dir = storage_dir or os.getcwd()
    os.makedirs(storage_dir, exist_ok=True)
    return storage_dir


def get_or_create_collection(client: str, name: str):
    """Return a collection handle (here, a dict with paths)."""
    paths = _paths_for(client, name)
    # ensure files exist
    if not os.path.exists(paths["index"]):
        # create empty IndexFlatIP with dimension unknown until first add
        # we will lazily create the index on first add
        pass
    return {"storage_dir": client, "name": name, "paths": paths}


def _load_index(paths: Dict[str, str]):
    if not FAISS_AVAILABLE:
        raise ImportError("faiss is not installed")
    index_path = paths["index"]
    if os.path.exists(index_path):
        try:
            return faiss.read_index(index_path)
        except Exception:
            # corrupt or incompatible index
            return None
    return None


def _load_ids_texts_metas(paths: Dict[str, str]):
    ids = []
    texts = []
    metas = []
    if os.path.exists(paths["ids"]):
        try:
            ids = np.load(paths["ids"], allow_pickle=True).tolist()
        except Exception:
            ids = []
    if os.path.exists(paths["texts"]):
        try:
            with open(paths["texts"], "r", encoding="utf-8") as f:
                texts = json.load(f)
        except Exception:
            texts = []
    if os.path.exists(paths["metas"]):
        try:
            with open(paths["metas"], "r", encoding="utf-8") as f:
                metas = json.load(f)
        except Exception:
            metas = []
    return ids, texts, metas


def add(col: Dict[str, Any], ids: Iterable[str], texts: Iterable[str], embeddings: List[List[float]], metadatas: Iterable[Dict[str, Any]]):
    if not FAISS_AVAILABLE:
        raise ImportError("faiss is not installed")
    paths = col["paths"]
    idx = _load_index(paths)
    ids_list, texts_list, metas_list = _load_ids_texts_metas(paths)

    embs = np.array(embeddings, dtype="float32")
    # normalize for cosine (use inner product on normalized vectors)
    norms = np.linalg.norm(embs, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    embs = embs / norms

    dim = embs.shape[1]
    if idx is None:
        # create new index
        idx = faiss.IndexFlatIP(dim)
    else:
        # ensure dim matches
        if idx.d != dim:
            # recreate index (drop old)
            idx = faiss.IndexFlatIP(dim)

    start_pos = idx.ntotal
    idx.add(embs)

    # update lists
    ids_list.extend(list(ids))
    texts_list.extend(list(texts))
    metas_list.extend(list(metadatas))

    # persist index and metadata
    tmp_index = paths["index"] + ".tmp"
    try:
        faiss.write_index(idx, tmp_index)
        os.replace(tmp_index, paths["index"])
    except Exception:
        pass

    np.save(paths["ids"], np.array(ids_list, dtype=object), allow_pickle=True)
    try:
        with open(paths["texts"], "w", encoding="utf-8") as f:
            json.dump(texts_list, f)
        with open(paths["metas"], "w", encoding="utf-8") as f:
            json.dump(metas_list, f)
    except Exception:
        pass


def query(col: Dict[str, Any], embedding: List[float], k: int = 5):
    if not FAISS_AVAILABLE:
        raise ImportError("faiss is not installed")
    paths = col["paths"]
    idx = _load_index(paths)
    ids_list, texts_list, metas_list = _load_ids_texts_metas(paths)
    if idx is None or idx.ntotal == 0:
        return []

    q = np.array(embedding, dtype="float32")
    qnorm = np.linalg.norm(q)
    if qnorm == 0:
        qnorm = 1.0
    q = q / qnorm
    q = q.reshape(1, -1)
    D, I = idx.search(q, k)
    results = []
    for score, pos in zip(D[0], I[0]):
        if pos < 0:
            continue
        doc_id = ids_list[pos] if pos < len(ids_list) else None
        text = texts_list[pos] if pos < len(texts_list) else None
        meta = metas_list[pos] if pos < len(metas_list) else None
        results.append({"id": doc_id, "text": text, "metadata": meta, "score": float(score)})
    return results


def persist(client: Any):
    # All operations write files immediately; nothing to do here.
    return


def delete_collection(client: str, name: str):
    paths = _paths_for(client, name)
    for p in paths.values():
        try:
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass


__all__ = ["client", "get_or_create_collection", "add", "query", "persist", "delete_collection"]
