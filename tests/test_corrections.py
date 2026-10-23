from src.extraction.corrections import apply_corrections


def test_fixes_section_word():
    out, ch = apply_corrections("فدفہ 45 کے تحت")
    assert "دفعہ 45" in out
    assert ch and ch[0]["count"] == 1


def test_fixes_haj_committee_phrase():
    out, _ch = apply_corrections("بھارتی جج کمیٹی کے نام سے")
    assert "حج کمیٹی" in out


def test_does_not_touch_judge():
    """'جج' alone means judge — it must NOT be rewritten."""
    out, ch = apply_corrections("جج نے فیصلہ دیا")
    assert out == "جج نے فیصلہ دیا"
    assert ch == []


def test_never_silent():
    _out, ch = apply_corrections("فدفہ 3 اور فدفہ 4")
    assert ch and ch[0]["count"] == 2


def test_clean_text_unchanged():
    clean = "اس ایکٹ کو حج کمیٹی ایکٹ، 2002 کہا جائے گا۔"
    out, ch = apply_corrections(clean)
    assert out == clean
    assert ch == []
