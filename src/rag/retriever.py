"""Query -> ranked chunks."""
from src.ingestion.vector_store import VectorStore


class Retriever:
    def __init__(self, store: VectorStore, embedder):
        self.store = store
        self.embedder = embedder

    def retrieve(self, question: str, k: int = 5, act: str | None = None):
        qvec = self.embedder.encode_one(question, kind="query")
        hits = self.store.search(qvec, k=k * 3 if act else k)
        if act:
            hits = [(c, s) for c, s in hits if c.get("act") == act][:k]
        return hits[:k]
