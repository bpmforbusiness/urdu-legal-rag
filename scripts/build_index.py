#!/usr/bin/env python3
"""Chunk every extracted act, embed the chunks, and persist the index."""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.expanduser("~/urdu_rag"))

from src.ingestion.chunker import chunks_from_act                  # noqa: E402
from src.ingestion.embedder import Embedder                        # noqa: E402
from src.ingestion.vector_store import VectorStore                 # noqa: E402

ROOT = os.path.expanduser("~/urdu_rag")
PROC = os.path.join(ROOT, "data/processed")
OUT = os.path.join(PROC, "index/urdu-legal")


def main() -> int:
    files = [f for f in sorted(glob.glob(os.path.join(PROC, "*.json")))
             if not os.path.basename(f).startswith("_")]
    chunks = []
    for f in files:
        d = json.load(open(f))
        cs = chunks_from_act(d)
        chunks.extend(cs)
        print(f"  {d['act'][:46]:48} sections={len(d.get('sections', [])):3d} chunks={len(cs):4d}")
    if not chunks:
        print("nothing to index")
        return 1
    print(f"\ntotal chunks: {len(chunks)}")
    emb = Embedder()
    print(f"embedding with {emb.model_name} ...")
    vecs = emb.encode([c["text"] for c in chunks], kind="passage")
    store = VectorStore()
    store.add(vecs, chunks)
    store.save(OUT)
    print(f"index saved -> {OUT}.npy  ({len(chunks)} vectors, dim {vecs.shape[1]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
