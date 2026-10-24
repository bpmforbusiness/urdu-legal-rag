"""FastAPI service: /health, /search (retrieval only), /ask (retrieval + generation)."""
import os
import sys

sys.path.insert(0, os.path.expanduser("~/urdu_rag"))

from fastapi import FastAPI                                  # noqa: E402
from pydantic import BaseModel                               # noqa: E402

from src.guardrails import input_guard, output_guard          # noqa: E402
from src.ingestion.embedder import Embedder                   # noqa: E402
from src.ingestion.vector_store import VectorStore            # noqa: E402
from src.rag.generator import Generator                       # noqa: E402
from src.rag.retriever import Retriever                       # noqa: E402

INDEX = os.path.expanduser("~/urdu_rag/data/processed/index/urdu-legal")

app = FastAPI(title="Urdu Legal RAG", version="0.2.0")
_state = {}


def _load():
    if "retriever" not in _state:
        store = VectorStore.load(INDEX)
        _state["retriever"] = Retriever(store, Embedder(),
                                          mode=os.environ.get("RETRIEVAL_MODE", "dense"))
        _state["generator"] = Generator()
    return _state["retriever"], _state["generator"]


class SearchIn(BaseModel):
    question: str
    k: int = 5
    act: str | None = None


class AskIn(SearchIn):
    generate: bool = True


@app.get("/health")
def health():
    ok = os.path.exists(INDEX + ".npy")
    n = len(VectorStore.load(INDEX).chunks) if ok else 0
    return {"status": "ok" if ok else "no_index", "chunks": n}


@app.post("/search")
def search(body: SearchIn):
    good, why = input_guard.check(body.question)
    if not good:
        return {"error": why}
    retriever, _ = _load()
    hits = retriever.retrieve(body.question, k=body.k, act=body.act)
    return {"results": [{"score": round(s, 4), "act": c["act"],
                         "section_no": c.get("section_no"), "page": c.get("page_start"),
                         "text": c["text"][:400]} for c, s in hits]}


@app.post("/ask")
def ask(body: AskIn):
    good, why = input_guard.check(body.question)
    if not good:
        return {"error": why}
    retriever, generator = _load()
    hits = retriever.retrieve(body.question, k=body.k, act=body.act)
    if not hits:
        return {"answer": "دیے گئے دستاویزات میں اس کا کوئی حوالہ نہیں ملا۔", "sources": []}
    answer = generator.answer(body.question, hits) if body.generate else ""
    ok, problems = output_guard.check(answer, hits)
    return {"answer": answer, "guardrails_ok": ok, "problems": problems,
            "sources": [{"act": c["act"], "section_no": c.get("section_no"),
                         "page": c.get("page_start"), "score": round(s, 4)} for c, s in hits]}
