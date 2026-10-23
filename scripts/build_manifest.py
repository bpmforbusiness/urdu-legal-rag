#!/usr/bin/env python3
"""Build data/processed/corpus_manifest.json + .csv (pages, bytes, sha256 per act)."""
import glob
import hashlib
import json
import os
import sys

import pymupdf as fitz

ROOT = os.path.expanduser("~/urdu_rag")
RAW = os.path.join(ROOT, "data/raw")
OUT = os.path.join(ROOT, "data/processed")
SOURCE = "https://www.urducouncil.nic.in/acts"


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for p in sorted(glob.glob(os.path.join(RAW, "*.pdf"))):
        rows.append({
            "act": os.path.basename(p)[:-4],
            "file": os.path.basename(p),
            "pages": fitz.open(p).page_count,
            "bytes": os.path.getsize(p),
            "sha256": hashlib.sha256(open(p, "rb").read()).hexdigest(),
        })
    doc = {"corpus": "NCPUL Urdu translations of Indian central acts",
           "source": SOURCE, "acts": len(rows),
           "pages": sum(r["pages"] for r in rows), "items": rows}
    json.dump(doc, open(os.path.join(OUT, "corpus_manifest.json"), "w"), indent=1)
    with open(os.path.join(OUT, "corpus_manifest.csv"), "w") as f:
        f.write("act,file,pages,bytes,sha256\n")
        for r in rows:
            f.write(f"{r['act']},{r['file']},{r['pages']},{r['bytes']},{r['sha256']}\n")
    print(f"{len(rows)} acts, {doc['pages']} pages -> {OUT}/corpus_manifest.{{json,csv}}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
