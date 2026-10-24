#!/usr/bin/env python3
"""Chunk every extracted act, embed the chunks, and persist the index."""
import argparse
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


def embed_text(c: dict, with_context: bool = True) -> str:
    """Text used for embedding only — the stored chunk keeps its clean text.

    Short sections lose to long ones under mean pooling: RTI s.3 is 96 chars and ranked
    54/866 for a query quoting it verbatim, while every top hit was 620-800 chars.
    Prefixing act + section context gives short chunks something to match on without
    changing what gets cited.
    """
    if not with_context:
        return c["text"]
    head = c["act"].replace("-", " ")
    if c.get("section_no"):
        head += f" — دفعہ {c['section_no']}"
    if c.get("section_title"):
        head += f": {str(c['section_title'])[:80]}"
    return f"{head}\n{c['text']}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-context", action="store_true",
                    help="embed raw chunk text (no act/section prefix)")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()

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
    print(f"\ntotal chunks: {len(chunks)} | context prefix: {not a.no_context}")
    emb = Embedder()
    print(f"embedding with {emb.model_name} ...")
    vecs = emb.encode([embed_text(c, not a.no_context) for c in chunks], kind="passage")
    store = VectorStore()
    store.add(vecs, chunks)
    store.save(a.out)
    print(f"index saved -> {a.out}.npy  ({len(chunks)} vectors, dim {vecs.shape[1]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
