# Corpus extraction results

Produced by `scripts/run_extraction.py` + `scripts/validate_corpus.py`, 2026-10-23/24.
Every figure below was read out of the extracted JSON, not estimated.

**Corpus:** 9 Urdu translations of Indian central acts, published by NCPUL
(`https://www.urducouncil.nic.in/acts`).

| Act | Pages | Characters | Urdu script | Sections | Warnings |
|---|---|---|---|---|---|
| The Right to Information Act, 2005 | 28 | 53,970 | 100% | 56 | 0 |
| The Legal Metrology Act, 2009 | 25 | 49,717 | 100% | 49 | 0 |
| The Protection of Women from Domestic Violence Act, 2005 | 15 | 30,152 | 100% | 38 | 0 |
| The Haj Committee Act, 2002 | 20 | 36,017 | 99% | 52 | 0 |
| The Commission for Protection of Child Rights Act, 2005 | 14 | 24,929 | 100% | 48 | 0 |
| The Maintenance and Welfare of Parents and Senior Citizens Act, 2007 | 13 | 20,560 | 100% | 36 | 0 |
| The Collection of Statistics Act, 2008 | 13 | 22,064 | 100% | 36 | 0 |
| The Science and Engineering Research Board Act, 2008 | 10 | 14,325 | 100% | 28 | 0 |
| The Gazette of India 04 (Central Act) | 110 | 169,744 | 98% | 60 | 6 |
| **Total** | **248** | **421,478** | **99%** | **403** | **6** |

## Notes

- **248/248 pages transcribed, 0 failures.** OCR is cached per page
  (`data/ocr_cache/`), so the corpus can be rebuilt without re-calling the API.
- **98–100% Urdu script ratio** across every act. This is the number that matters: the
  source PDFs contain **zero** Urdu codepoints in their text layer, so everything here came
  from rasterising and re-reading the pages.
- The gazette's 6 warnings are low-Urdu pages — its **English** front matter, index and
  section headings. Expected for a bilingual gazette, and flagged rather than silently kept.
- **403 sections** were split out with page-level provenance, so an answer can cite
  `act → section → page`.

## Failure modes observed (and how they were handled)

| Symptom | Cause | Handling |
|---|---|---|
| HTTP 429 `GoUsageLimitError` | workspace usage cap on the OCR endpoint | retried; recovered. Cache means only gaps are re-run |
| HTTP 400 `invalid_request_error` | transient upstream errors, scattered single pages | 4 retries with backoff; all eventually succeeded |
| HTTP 403 `code 1010` | Cloudflare rejects Python's default User-Agent | `User-Agent` header sent (see `ocr.py`) |
| an act silently extracted 0 pages | a bug: page bookkeeping was gated behind `if fixed:` | fixed; `run_extraction.py` now **refuses** to overwrite a good extraction with an empty one |

That last row is the important one. The pipeline is allowed to fail loudly, and it is **not**
allowed to destroy a previous good result with a silent empty one.
