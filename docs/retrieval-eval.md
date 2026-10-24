# Retrieval evaluation

Measured on the extracted corpus (403 sections → 866 chunks) against 9 hand-verified Urdu
questions. Each question's answer was confirmed against the extracted section text before
being added (`verified_against` in `data/evaluation/retrieval_questions.json`).

Reproduce:

```bash
.venv/bin/python scripts/evaluate_retrieval.py --mode dense     # or lexical / hybrid
```

## Results

| Mode | Recall@1 | Recall@3 | Recall@5 | MRR |
|---|---|---|---|---|
| **dense** (multilingual-E5-small) | **0.444** | **0.778** | **0.778** | **0.574** |
| hybrid (dense + BM25, RRF) | 0.333 | 0.778 | 0.778 | 0.519 |
| lexical (BM25 only) | 0.111 | 0.444 | 0.667 | 0.304 |

**Default is `dense`** — it won, so it is what ships.

## What this shows — including a hypothesis that failed

I expected **hybrid retrieval to beat dense** on legal text, on the theory that distinctive
lexical anchors (act names, `دفعہ 4`, `باب II`) survive poorly in dense embeddings. The
measurement says otherwise:

- **BM25 alone is very weak here: Recall@1 0.111.** Three of nine questions have their answer
  somewhere in the top 5 but almost never first. Urdu is heavily inflected, particles attach
  to words, and the question's wording rarely matches the statute's wording token-for-token.
  A naive whitespace/punctuation tokenizer with a short stopword list is not enough.
- **Fusion actively hurt.** RRF pulled Recall@1 down from 0.444 to 0.333: adding a weak ranker
  as an equal partner dilutes a stronger one. Equal-weight RRF assumes the systems are
  comparably good, and they are not.

So the hybrid path is **implemented, tested and available** (`--mode hybrid`) but **not the
default**, and it should not be re-enabled without a better Urdu lexical analyser
(stemming / light verb stripping) — otherwise it is a regression dressed as sophistication.

## Known limitations

- **9 questions is a small set.** Treat the absolute numbers as indicative, not precise. Each
  question is worth 11 points of Recall@1, so single-question differences are noise.
- **Similarity scores are compressed** (≈0.85–0.90 across near and distant chunks). With 866
  chunks in one legal register, cosine similarity barely separates relevant from irrelevant —
  which is exactly why rank-1 is the unstable metric here, and why Recall@3 is the more
  trustworthy number.
- **Two questions in the original 4-question set were bad**, not the retriever. One asked
  *"where are the definitions given in this act?"* without naming the act — every one of the
  nine acts has a definitions section, so returning another act's definitions was defensible.
  It is now act-scoped, with the reason recorded in the question file. Fixing questions is
  part of evaluation; leaving a bad question in and blaming the system is not.
- **Duplicate section numbers exist** in the extraction (e.g. the Domestic Violence Act has
  two entries numbered 3, and acts with an index produce spurious low-numbered "sections").
  Chunk provenance is still correct (page-level), but section-number matching in the evaluator
  can be satisfied by the wrong duplicate.

## Next step that would actually move the needle

1. **A stronger embedder** — BGE-M3 (multilingual, 8192-token context) is the obvious upgrade
   over E5-small for long legal passages. One config change: `EMBED_MODEL=BAAI/bge-m3`.
2. **A bigger question set** (~50) so Recall@1 differences are meaningful.
3. Only then revisit hybrid, with a real Urdu analyser.
