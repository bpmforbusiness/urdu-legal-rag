#!/usr/bin/env python3
"""Retrieval quality: Recall@1/3/5 and MRR against a labelled Urdu question set.

Questions live in data/evaluation/retrieval_questions.json:
    [{"question": "...", "act": "...", "section_no": "3"}]
"""
import json
import os
import sys

sys.path.insert(0, os.path.expanduser("~/urdu_rag"))

from src.ingestion.embedder import Embedder                        # noqa: E402
from src.ingestion.vector_store import VectorStore                 # noqa: E402
from src.rag.retriever import Retriever                            # noqa: E402

ROOT = os.path.expanduser("~/urdu_rag")
INDEX = os.path.join(ROOT, "data/processed/index/urdu-legal")
QS = os.path.join(ROOT, "data/evaluation/retrieval_questions.json")


def main() -> int:
    if not os.path.exists(QS):
        print(f"no labelled questions at {QS}")
        return 1
    qs = json.load(open(QS))
    retriever = Retriever(VectorStore.load(INDEX), Embedder())
    hits_at = {1: 0, 3: 0, 5: 0}
    rr = 0.0
    for item in qs:
        hits = retriever.retrieve(item["question"], k=5)
        rank = None
        for i, (c, _s) in enumerate(hits, start=1):
            same_sec = str(c.get("section_no") or "") == str(item.get("section_no") or "")
            same_act = (not item.get("act")) or c["act"] == item["act"]
            if same_sec and same_act:
                rank = i
                break
        for k in hits_at:
            if rank and rank <= k:
                hits_at[k] += 1
        if rank:
            rr += 1.0 / rank
    n = len(qs)
    print(f"questions: {n}")
    for k in (1, 3, 5):
        print(f"  Recall@{k}: {hits_at[k] / n:.4f}")
    print(f"  MRR:       {rr / n:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
