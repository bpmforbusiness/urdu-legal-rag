"""Urdu text normalisation: digits, diacritics, variant letters, RTL noise."""
import re
import unicodedata

ARABIC_INDIC = {ord(c): str(i) for i, c in enumerate("٠١٢٣٤٥٦٧٨٩")}
EXT_ARABIC_INDIC = {ord(c): str(i) for i, c in enumerate("۰۱۲۳۴۵۶۷۸۹")}

TATWEEL = "\u0640"
DIACRITICS = "".join(chr(c) for c in list(range(0x064B, 0x0660)) + [0x0670])
ZERO_WIDTH = "".join(chr(c) for c in (0x200B, 0x200C, 0x200D, 0x200E, 0x200F,
                                      0x202A, 0x202B, 0x202C, 0x202D, 0x202E, 0xFEFF))

# OCR and legacy fonts confuse these; fold to the common Urdu form.
LETTER_FOLD = {
    "\u0622": "\u0627",   # آ -> ا
    "\u0623": "\u0627",   # أ -> ا
    "\u0625": "\u0627",   # إ -> ا
    "\u0649": "\u06CC",   # ى -> ی
    "\u064A": "\u06CC",   # ي -> ی
    "\u06C1": "\u06C1",   # ھ kept (distinct in Urdu)
    "\u06A9": "\u06A9",   # ک kept
    "\u0629": "\u06C1",   # ة -> ھ
}


def to_ascii_digits(text: str) -> str:
    return text.translate(ARABIC_INDIC).translate(EXT_ARABIC_INDIC)


def strip_diacritics(text: str) -> str:
    return text.translate({ord(c): None for c in DIACRITICS + TATWEEL})


def strip_zero_width(text: str) -> str:
    return text.translate({ord(c): None for c in ZERO_WIDTH})


def fold_letters(text: str) -> str:
    return text.translate(str.maketrans(LETTER_FOLD))


def collapse_space(text: str) -> str:
    text = re.sub(r"[ \t\u00A0]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return "\n".join(line.strip() for line in text.split("\n")).strip()


def normalize(text: str, fold: bool = True) -> str:
    """Full normalisation used before section splitting and indexing."""
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    text = strip_zero_width(text)
    text = to_ascii_digits(text)
    text = strip_diacritics(text)
    if fold:
        text = fold_letters(text)
    return collapse_space(text)


def arabic_ratio(text: str) -> float:
    total = arabic = 0
    for ch in text:
        if ch.isalpha():
            total += 1
            if "\u0600" <= ch <= "\u06ff":
                arabic += 1
    return round(arabic / total, 4) if total else 0.0


def looks_like_urdu(text: str, threshold: float = 0.5) -> bool:
    """Guardrail: reject OCR output that is not predominantly Urdu script."""
    return arabic_ratio(text) >= threshold
