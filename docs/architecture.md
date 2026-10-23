# Architecture

## Why this is not a copy of the Arabic project

The Arabic project's phase 1 was *extraction*: two-column PDFs with a real text layer and a
column-aware spatial parser. This corpus inverts that problem. The PDFs are single-column,
visually clean, and **digitally empty** — a text layer exists but carries no Unicode. So the
hard part moves from *layout reconstruction* to *OCR quality and provenance*.

## Stages

1. **Render** (`render.py`) — each page to PNG at a configurable DPI. 200 DPI is the default:
   enough for Nastaliq strokes, small enough for a vision model.
2. **OCR** (`ocr.py`) — one VLM call per page, with:
   - a disk cache keyed by `sha256(pdf bytes + page + model + max_px)`, so re-runs are free;
   - retry with jitter (vision endpoints return transient empties);
   - a JSON sidecar per page holding the raw transcription and the model used.
3. **Normalise** (`normalize.py`) — Urdu-specific clean-up:
   - Arabic-Indic (٠-٩) and extended Arabic-Indic (۰-۹) digits → ASCII;
   - strip tatweel/kashida (`\u0640`) and optional diacritics;
   - normalise the alef/yeh/heh variants that OCR and legacy fonts mix up;
   - collapse the ZWNJ/ZWJ noise RTL extraction produces, collapse whitespace.
4. **Split** (`sections.py`) — Urdu legal structure: `باب` (chapter), `دفعہ` (section),
   `تعریفات` (definitions), `(1)`, `(الف)`, `(ب)`. Emits a section tree with page anchors.
5. **Chunk / index / retrieve** — not yet built.

## Provenance

Every record carries `act`, `page`, `section_no`, `section_title`, `ocr_model`, `ocr_sha`.
Chunk IDs are deterministic (`act:page:section`), so a citation can always be traced back to
a rendered page image.

## Evaluation (planned)

- Retrieval: Recall@1/3/5 and MRR against a hand-labelled Urdu question set.
- Generation: faithfulness / context precision / context recall / answer relevancy, with a
  CI quality gate that fails the build below a threshold — the Arabic project's best idea.
