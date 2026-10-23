from src.extraction.sections import split_sections


TEXT = """باب اول
تعریفات۔۔ 2۔ اس ایکٹ میں
(الف) ’’چیئر پرسن‘‘ سے مراد ہے؛
دفعہ 3۔ کمیشن کا قیام
(1) مرکزی حکومت ایک کمیشن قائم کرے گی۔
دفعہ 4۔ کمیشن کے فرائض
کمیشن کی ذمہ داریاں ہوں گی۔"""

# The dominant style in the NCPUL corpus: a bare number + separator as the heading.
TEXT_NUMERIC = """باب I
ابتدائیہ
مختصر نام اور دست۔
(1)۔ اس ایکٹ کو حج کمیٹی ایکٹ، 2002 کہا جائے گا۔
2- اس ایکٹ میں بجائے اس کے کہ سیاق عبارت سے معلوم ہو۔
(الف) ”ڈیلی ٹاؤنمینٹ“ سے مراد ہے۔
2A۔ کچھ اور بات
3۔ کمیشن کا قیام
(1) مرکزی حکومت ایک کمیشن قائم کرے گی۔"""


def test_finds_sections_and_chapter():
    secs = split_sections("test-act", TEXT, lambda _o: 1)
    kinds = [s.kind for s in secs]
    assert "chapter" in kinds
    assert "definitions" in kinds
    assert kinds.count("section") >= 2


def test_section_numbers():
    secs = split_sections("test-act", TEXT, lambda _o: 1)
    nums = {s.section_no for s in secs if s.kind == "section"}
    assert {"3", "4"} <= nums


def test_page_mapping_is_used():
    secs = split_sections("test-act", TEXT, lambda o: 5 if o > 60 else 1)
    assert any(s.page_start == 5 for s in secs)


def test_numeric_heading_style():
    """The NCPUL corpus marks sections as '2- ...' / '3۔ ...', not 'دفعہ 2'."""
    secs = split_sections("test-act", TEXT_NUMERIC, lambda _o: 1)
    nums = [s.section_no for s in secs if s.kind == "section"]
    assert "2" in nums
    assert "3" in nums


def test_subclause_is_not_a_section():
    """'(1)۔ ...' is a sub-clause and must not be read as section 1."""
    secs = split_sections("test-act", TEXT_NUMERIC, lambda _o: 1)
    assert "1" not in [s.section_no for s in secs if s.kind == "section"]
