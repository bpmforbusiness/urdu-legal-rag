"""Minimal BM25 over chunk texts. Pure Python — no extra dependency.

Legal queries hinge on distinctive lexical anchors (act names, 'دفعہ 4', 'باب II') that
dense embeddings of same-register legal Urdu smear together, so lexical scoring earns its
place alongside the vectors.
"""
import math
import re
from collections import Counter

TOKEN = re.compile(r"[\w\u0600-\u06FF]+", re.UNICODE)
STOPWORDS = {"کا", "کی", "کے", "سے", "میں", "اور", "پر", "ہو", "ہے", "ہیں", "کو", "نے", "یہ", "وہ"}


def tokenize(text: str) -> list[str]:
    return [t for t in TOKEN.findall((text or "").lower()) if t not in STOPWORDS and len(t) > 1]


class BM25:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.docs: list[Counter] = []
        self.lens: list[int] = []
        self.df: Counter = Counter()
        self.avg_len = 0.0

    def fit(self, texts: list[str]):
        self.docs, self.lens = [], []
        self.df = Counter()
        for t in texts:
            toks = tokenize(t)
            c = Counter(toks)
            self.docs.append(c)
            self.lens.append(len(toks))
            for term in c:
                self.df[term] += 1
        self.avg_len = (sum(self.lens) / len(self.lens)) if self.lens else 0.0
        self.n = len(self.docs)
        return self

    def scores(self, query: str) -> list[float]:
        q = tokenize(query)
        out = [0.0] * self.n
        if not q or not self.n:
            return out
        for term in q:
            df = self.df.get(term, 0)
            if not df:
                continue
            idf = math.log(1 + (self.n - df + 0.5) / (df + 0.5))
            for i, doc in enumerate(self.docs):
                tf = doc.get(term, 0)
                if not tf:
                    continue
                dl = self.lens[i] or 1
                out[i] += idf * (tf * (self.k1 + 1)) / (
                    tf + self.k1 * (1 - self.b + self.b * dl / (self.avg_len or 1)))
        return out
