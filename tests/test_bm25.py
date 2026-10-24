from src.rag.bm25 import BM25, tokenize


DOCS = ["حج کمیٹی ایکٹ 2002 کا قیام", "اطلاع حاصل کرنے کا حق ہوگا", "ناپ اور تول کی بنیادی اکائیاں"]


def test_tokenize_drops_stopwords():
    assert "کی" not in tokenize("ناپ اور تول کی بنیادی اکائیاں")
    assert "ناپ" in tokenize("ناپ اور تول کی بنیادی اکائیاں")


def test_scores_rank_the_right_doc_first():
    b = BM25().fit(DOCS)
    s = b.scores("اطلاع حاصل کرنے کا حق")
    assert int(max(range(len(s)), key=lambda i: s[i])) == 1


def test_unseen_term_scores_zero():
    b = BM25().fit(DOCS)
    assert max(b.scores("کوئی ایسا لفظ جو نہیں ہے")) == 0


def test_empty_query_is_safe():
    b = BM25().fit(DOCS)
    assert b.scores("") == [0.0] * len(DOCS)
