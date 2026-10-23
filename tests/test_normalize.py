from src.extraction.normalize import (arabic_ratio, looks_like_urdu, normalize,
                                      to_ascii_digits)


def test_arabic_indic_digits_become_ascii():
    assert to_ascii_digits("دفعہ ۲۰۰۵") == "دفعہ 2005"


def test_extended_arabic_indic_digits():
    assert to_ascii_digits("۱۹۹۰") == "1990"


def test_diacritics_and_tatweel_removed():
    assert "\u0640" not in normalize("کــتاب")
    assert "\u064e" not in normalize("کَتاب")


def test_zero_width_removed():
    assert "\u200c" not in normalize("دفعہ\u200c2")


def test_alef_variants_fold():
    # آ / أ / إ all fold to bare alef ا
    assert normalize("آئین") == normalize("ائین")
    assert normalize("آن") == "ان"


def test_urdu_ratio_guard():
    assert looks_like_urdu("دفعہ 2۔ تعریفات")
    assert not looks_like_urdu("Section 2. Definitions")


def test_ratio_bounds():
    assert 0.0 <= arabic_ratio("دفعہ 2 ABC") <= 1.0
