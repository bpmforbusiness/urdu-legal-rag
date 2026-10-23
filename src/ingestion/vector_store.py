"""Vector store: numpy exact cosine search, with an optional FAISS path.

At corpus scale (~1-2k chunks) exact search is instant and dependency-free; FAISS is
offered for when the corpus grows.
"""
import json
import os

import numpy as np


class VectorStore:
    def __init__(self, dim: int | None = None):
        self.vectors: np.ndarray | None = None
        self.chunks: list[dict] = []
        self.dim = dim

    def add(self, vectors, chunks: list[dict]):
        arr = np.asarray(vectors, dtype=np.float32)
        if arr.ndim == 1:
            arr = arr.reshape(1, -1)
        arr /= (np.linalg.norm(arr, axis=1, keepdims=True) + 1e-12)
        self.vectors = arr if self.vectors is None else np.vstack([self.vectors, arr])
        self.chunks.extend(chunks)

    def search(self, qvec, k: int = 5) -> list[tuple[dict, float]]:
        if self.vectors is None or not len(self.chunks):
            return []
        q = np.asarray(qvec, dtype=np.float32).ravel()
        q /= (np.linalg.norm(q) + 1e-12)
        sims = self.vectors @ q
        k = min(k, len(sims))
        top = np.argpartition(-sims, k - 1)[:k]
        top = top[np.argsort(-sims[top])]
        return [(self.chunks[i], float(sims[i])) for i in top]

    def save(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        np.save(path + ".npy", self.vectors if self.vectors is not None
                else np.zeros((0, 0), dtype=np.float32))
        json.dump(self.chunks, open(path + ".chunks.json", "w"), ensure_ascii=False, indent=1)

    @classmethod
    def load(cls, path: str) -> "VectorStore":
        store = cls()
        store.vectors = np.load(path + ".npy")
        store.chunks = json.load(open(path + ".chunks.json"))
        return store
