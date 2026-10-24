# Urdu Legal RAG — Q&A over Urdu translations of Indian central acts

A retrieval-augmented pipeline for **Urdu legal text**, built on the nine Urdu-translated
central acts published by the National Council for Promotion of Urdu Language (NCPUL).

Modelled on the architecture of an Arabic legal RAG project, with one important difference:
that corpus had a usable text layer, **this one does not** — see *Why OCR* below.

## The corpus

`https://www.urducouncil.nic.in/acts` — 9 Urdu translations of central acts:

- The Right to Information Act, 2005
- The Protection of Women from Domestic Violence Act, 2005
- The Commission for Protection of Child Rights Act, 2005
- The Maintenance and Welfare of Parents and Senior Citizens Act, 2007
- The Haj Committee Act, 2002
- The Legal Metrology Act, 2009
- The Collection of Statistics Act, 2008
- The Science and Engineering Research Board Act, 2008
- The Gazette of India 04 (Central Act)

## Why OCR

These PDFs *look* digital but are not usable as text:

```
pages: 110 · extractable characters: 137,377 · Arabic-script characters: 0
script profile: 99% private-use-area codepoints
```

The files are typeset in legacy Urdu fonts (embedded as `FNTSBS+F15` … `F31`) with **no
ToUnicode mapping**, so every extractable character is a glyph index, not a letter. Naive
`PyMuPDF`/`pdfplumber` extraction returns gibberish; there is nothing to clean up.

So the pipeline **rasterises each page and transcribes it with a vision-language model**,
then normalises the result. That choice is a deliberate trade: VLM OCR reads Nastaliq far
better than Tesseract's `urd` model, at the cost of one API call per page and the need to
cache aggressively.

## Pipeline

```
PDF ──render──► page PNGs ──VLM OCR──► raw Urdu text (cached per page)
   ──normalise──► clean Urdu ──split──► sections (دفعہ) ──chunk──► JSON + FAISS
```

Every chunk keeps **page-level provenance** (act, page, section number) so answers can cite
the section they came from — non-negotiable for legal material.

## Layout

```
urdu-legal-rag/
├── src/
│   ├── extraction/     render.py · ocr.py · normalize.py · sections.py · schema.py
│   ├── ingestion/      chunker.py · embedder.py · vector_store.py
│   ├── rag/            retriever.py · prompt_builder.py · generator.py
│   ├── guardrails/     input_guard.py · output_guard.py
│   └── api/            main.py
├── scripts/            fetch_corpus.py · run_extraction.py · validate_corpus.py · build_index.py
├── tests/
├── data/               raw/ · processed/ · evaluation/ · ocr_cache/
└── docs/architecture.md
```

## Status

| Stage | State |
|---|---|
| Corpus acquisition | working — `scripts/fetch_corpus.py` |
| Page rendering | working — `src/extraction/render.py` |
| VLM OCR | working — `src/extraction/ocr.py` (cached per page) |
| Urdu normalisation | working — `src/extraction/normalize.py` |
| OCR post-correction | working — `src/extraction/corrections.py` (phrase-level, audited) |
| Section splitting | working — `src/extraction/sections.py` |
| Extraction pipeline | working — **248/248 pages, 421,478 chars, 403 sections** |
| Corpus validation | working — `scripts/validate_corpus.py` |
| Chunking + indexing | working — **866 chunks**, multilingual-E5-small, 384-dim |
| Retrieval | working — dense by default; lexical + hybrid available |
| Retrieval evaluation | working — R@1 0.444, R@3 0.778, MRR 0.574 (9 verified questions) |
| Generation + API | built — `src/api/main.py` (`/health`, `/search`, `/ask`) |

See `docs/corpus-results.md` for the extraction numbers and `docs/retrieval-eval.md` for the
retrieval ablation (including a hypothesis that the measurement disproved).

## Quickstart

```bash
cp .env.example .env      # add your OCR API key
python3 scripts/fetch_corpus.py
python3 scripts/run_extraction.py --limit-pages 5      # smoke test
python3 scripts/run_extraction.py                      # full corpus (long)
python3 scripts/validate_corpus.py
```
