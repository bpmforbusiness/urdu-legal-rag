"""Query -> ranked chunks. Dense, lexical (BM25), or hybrid via RRF."""
import numpy as np

from src.ingestion.vector_store import VectorStore
from src.rag.bm25 import BM25

RRF_K = 60          # standard Reciprocal Rank Fusion constant


class Retriever:
    def __init__(self, store: VectorStore, embedder, mode: str = "dense"):
        self.store = store
        self.embedder = embedder
        self.mode = mode
        self._bm25 = None

    @property
    def bm25(self) -> BM25:
        if self._bm25 is None:
            self._bm25 = BM25().fit([c.get("text", "") for c in self.store.chunks])
        return self._bm25

    def _dense_rank(self, question: str, k: int):
        qvec = self.embedder.encode_one(question, kind="query")
        return self.store.search(qvec, k=k)

    def _lex_rank(self, question: str, k: int):
        sc = self.bm25.scores(question)
        if not sc:
            return []
        idx = np.argsort(-np.asarray(sc))[:k]
        return [(self.store.chunks[i], float(sc[i])) for i in idx if sc[i] > 0]

    def retrieve(self, question: str, k: int = 5, act: str | None = None):
        pool = max(k * 4, 20)
        if self.mode == "dense":
            hits = self._dense_rank(question, pool)
        elif self.mode == "lexical":
            hits = self._lex_rank(question, pool)
        else:
            dense = self._dense_rank(question, pool)
            lex = self._lex_rank(question, pool)
            # Reciprocal Rank Fusion: robust without score normalisation
            fused: dict[str, float] = {}
            by_id: dict[str, dict] = {}
            for ranked in (dense, lex):
                for rank, (chunk, _score) in enumerate(ranked, start=1):
                    cid = chunk["chunk_id"]
                    by_id[cid] = chunk
                    fused[cid] = fused.get(cid, 0.0) + 1.0 / (RRF_K + rank)
            hits = [(by_id[cid], sc) for cid, sc in
                    sorted(fused.items(), key=lambda x: -x[1])]
        if act:
            hits = [(c, s) for c, s in hits if c.get("act") == act]
        return hits[:k]
