#!/usr/bin/env python3
"""Render -> OCR -> normalise -> split, for one act or the whole corpus.

    python3 scripts/run_extraction.py --limit-pages 3
    python3 scripts/run_extraction.py --act "The-Haj-Committee-Act-2002.pdf"
"""
import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.expanduser("~/urdu_rag"))

from src.extraction.corrections import apply_corrections, summarize
from src.extraction.normalize import arabic_ratio, looks_like_urdu, normalize   # noqa: E402
from src.extraction.ocr import OcrClient, OcrError                              # noqa: E402
from src.extraction.render import page_count, render_pages                      # noqa: E402
from src.extraction.sections import split_sections                              # noqa: E402

ROOT = os.path.expanduser("~/urdu_rag")
RAW = os.path.join(ROOT, "data/raw")
PROC = os.path.join(ROOT, "data/processed")


def extract_act(pdf: str, client: OcrClient, limit_pages: int | None, dpi: int,
                workers: int = 5) -> dict:
    from concurrent.futures import ThreadPoolExecutor

    act = os.path.basename(pdf).replace(".pdf", "")
    total = page_count(pdf)
    last = min(limit_pages, total) if limit_pages else total
    pages_dir = os.path.join(ROOT, "data/pages", act)
    print(f"\n=== {act} ({total} pages, rendering {last}) ===", flush=True)

    imgs = render_pages(pdf, pages_dir, dpi=dpi, first=1, last=last)

    def one(idx_img):
        idx, img = idx_img
        try:
            return idx, client.transcribe(img, idx), None
        except OcrError as exc:
            return idx, None, f"page {idx}: {exc}"

    page_texts, page_nums, warnings = [], [], []
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        for idx, rec, err in pool.map(one, list(enumerate(imgs, start=1))):
            if err:
                warnings.append(err)
                print(f"  page {idx}: OCR FAILED", flush=True)
                continue
            clean = normalize(rec["text"])
            clean, fixed = apply_corrections(clean)
            if fixed:
                print(f"  page {idx}: corrections: {summarize(fixed)}", flush=True)
            ratio = arabic_ratio(clean)
            flag = "ok " if looks_like_urdu(clean) else "LOW"
            print(f"  page {idx}: {len(clean):5d} chars, urdu {ratio:5.1%} [{flag}]"
                  f"{' (cached)' if rec.get('cached') else ''}", flush=True)
            if not looks_like_urdu(clean):
                warnings.append(f"page {idx}: only {ratio:.0%} Urdu script")
            page_texts.append(clean)
            page_nums.append(idx)

    # character offsets -> page numbers, for section provenance
    offsets, running = [], 0
    for num, txt in zip(page_nums, page_texts):
        offsets.append((running, num))
        running += len(txt) + 1

    def page_of(off: int) -> int:
        page = 1
        for start, num in offsets:
            if off >= start:
                page = num
            else:
                break
        return page

    joined = "\n".join(page_texts)
    sections = split_sections(act, joined, page_of) if joined else []

    result = {"act": act, "pdf": os.path.basename(pdf), "pages": total,
              "pages_ocred": len(page_texts),
              "chars": len(joined), "urdu_ratio": arabic_ratio(joined),
              "sections": [s.model_dump() for s in sections], "warnings": warnings}
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--act", help="only this PDF filename in data/raw")
    ap.add_argument("--limit-pages", type=int, help="render only the first N pages")
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--workers", type=int, default=5, help="parallel OCR calls (default 5)")
    a = ap.parse_args()

    os.makedirs(PROC, exist_ok=True)
    pdfs = ([os.path.join(RAW, a.act)] if a.act
            else sorted(glob.glob(os.path.join(RAW, "*.pdf"))))
    client = OcrClient()
    summary = []
    for pdf in pdfs:
        if not os.path.exists(pdf):
            print("missing:", pdf)
            continue
        res = extract_act(pdf, client, a.limit_pages, a.dpi, workers=a.workers)
        out = os.path.join(PROC, res["act"] + ".json")
        # Guard: never let an empty/failed run destroy a previously good extraction.
        if os.path.exists(out) and res["pages_ocred"] == 0:
            try:
                prev = json.load(open(out))
            except Exception:                                       # noqa: BLE001
                prev = {}
            if prev.get("pages_ocred", 0) > 0:
                print(f"  !! REFUSING to overwrite {os.path.basename(out)} with an empty "
                      f"result (previous run had {prev['pages_ocred']} pages, "
                      f"{prev.get('chars', 0)} chars)")
                summary.append({"act": res["act"], "pages_ocred": prev["pages_ocred"],
                                "chars": prev.get("chars", 0),
                                "urdu_ratio": prev.get("urdu_ratio", 0),
                                "sections": len(prev.get("sections", [])),
                                "warnings": len(prev.get("warnings", [])), "out": out,
                                "note": "kept previous extraction (new run was empty)"})
                continue
        json.dump(res, open(out, "w"), ensure_ascii=False, indent=1)
        summary.append({"act": res["act"], "pages_ocred": res["pages_ocred"],
                        "chars": res["chars"], "urdu_ratio": res["urdu_ratio"],
                        "sections": len(res["sections"]), "warnings": len(res["warnings"]),
                        "out": out})
        print(f"  -> {out}  sections={len(res['sections'])} warnings={len(res['warnings'])}")

    json.dump(summary, open(os.path.join(PROC, "_extraction_summary.json"), "w"),
              ensure_ascii=False, indent=1)
    print("\n=== summary ===")
    for s in summary:
        print(f"  {s['act'][:44]:46} pages={s['pages_ocred']:3d} chars={s['chars']:6d} "
              f"urdu={s['urdu_ratio']:.0%} sections={s['sections']:3d} warn={s['warnings']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
