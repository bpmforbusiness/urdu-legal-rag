from src.ingestion.chunker import chunk_id, chunks_from_act, citation, split_long

ACT = {"act": "The-Haj-Committee-Act-2002", "sections": [
    {"kind": "chapter", "title": "باب I", "text": "باب I\\nابتدائیہ", "page_start": 1, "page_end": 1},
    {"kind": "section", "section_no": "3", "title": "3۔ کمیٹی کا قیام",
     "text": "3۔ (1) بھارتی حج کمیٹی کے نام سے ایک کمیٹی تشکیل دی جائے گی۔ " * 30,
     "page_start": 2, "page_end": 3},
]}


def test_chunks_keep_provenance():
    cs = chunks_from_act(ACT)
    assert cs
    for c in cs:
        assert c["act"] == "The-Haj-Committee-Act-2002"
        assert c["page_start"] >= 1
        assert c["chunk_id"]


def test_section_number_propagates():
    cs = [c for c in chunks_from_act(ACT) if c["section_no"] == "3"]
    assert cs and all(c["section_no"] == "3" for c in cs)


def test_long_section_is_split():
    cs = [c for c in chunks_from_act(ACT) if c["section_no"] == "3"]
    assert len(cs) > 1


def test_chunk_ids_are_deterministic():
    assert chunk_id("a", "1", 2, 0) == chunk_id("a", "1", 2, 0)
    assert chunk_id("a", "1", 2, 0) != chunk_id("a", "1", 2, 1)


def test_split_long_respects_max():
    parts = split_long("x" * 3000, max_chars=800)
    assert len(parts) > 1
    assert all(len(p) <= 1100 for p in parts)


def test_citation_mentions_section_and_page():
    c = chunks_from_act(ACT)[-1]
    cite = citation(c)
    assert "section" in cite and "p" in cite
