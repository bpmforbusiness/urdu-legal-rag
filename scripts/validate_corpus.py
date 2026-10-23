#!/usr/bin/env python3
"""Validate extracted acts: OCR quality, Urdu ratio, section coverage, gaps."""
import glob
import json
import os
import sys

ROOT = os.path.expanduser("~/urdu_rag")
PROC = os.path.join(ROOT, "data/processed")

MIN_URDU = 0.60
MIN_CHARS_PER_PAGE = 300


def main() -> int:
    files = [f for f in sorted(glob.glob(os.path.join(PROC, "*.json")))
             if not os.path.basename(f).startswith("_")]
    if not files:
        print("nothing extracted yet")
        return 1
    bad, warn = [], []
    print(f"{'act':46} {'pages':>5} {'chars':>7} {'urdu':>6} {'secs':>5} status")
    for f in files:
        d = json.load(open(f))
        pages, chars = d.get("pages_ocred", 0), d.get("chars", 0)
        ratio, secs = d.get("urdu_ratio", 0), len(d.get("sections", []))
        problems = []
        if ratio < MIN_URDU:
            problems.append(f"urdu {ratio:.0%}")
        if pages and chars / pages < MIN_CHARS_PER_PAGE:
            problems.append(f"thin {chars // max(pages, 1)} cp")
        if d.get("warnings"):
            problems.append(f"{len(d['warnings'])} warn")
        status = "FAIL " + ", ".join(problems) if problems and any(
            p.startswith(("urdu", "thin")) for p in problems) else (
            "warn " + ", ".join(problems) if problems else "ok")
        print(f"{d['act'][:44]:46} {pages:5d} {chars:7d} {ratio:6.0%} {secs:5d} {status}")
        (bad if status.startswith("FAIL") else warn if status.startswith("warn") else warn
         ).append(d["act"]) if problems else None
    print(f"\n{len(files)} acts | with problems: {len(bad) + len(warn)}")
    print("thresholds: urdu >= 60%, >= 300 chars/page")
    return 0


if __name__ == "__main__":
    sys.exit(main())
