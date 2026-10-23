"""Split normalised Urdu act text into sections (دفعہ) and chapters (باب)."""
import re

from src.extraction.schema import Section

# Urdu structure markers
CHAPTER = "\u0628\u0627\u0628"                    # باب   (chapter)
SECTION_WORD = "\u062f\u0641\u0639\u06c1"        # دفعہ  (section)
DEFINITIONS = "\u062a\u0639\u0631\u06cc\u0641\u0627\u062a"  # تعریفات (definitions)

CHAPTER_RE = re.compile(rf"^\s*({CHAPTER}\s*[-–—:\.]?\s*.{{0,60}})$", re.M)
DEFS_RE = re.compile(rf"^\s*({DEFINITIONS}\s*[\-–—۔:\.]*)", re.M)
# Headings in this corpus are usually a bare number followed by a separator:
#   "2- اس ایکٹ میں ..."   /   "3۔ کمیشن کا قیام"
# Sub-clauses start with "(" — "(1)۔ ..." — and must NOT match.
NUM_HEADING_RE = re.compile(r"^\s*(\d{1,3})\s*[-–—۔:]\s*(\S.*)$", re.M)
# Some acts do label headings with the word; OCR sometimes renders د as ف ("فدفہ").
WORD_HEADING_RE = re.compile(rf"^\s*[دف]\u0641\u0639\u06c1\s*(\d{{1,3}})")


def _heading_of(line: str):
    """Return (kind, section_no, title) if the line opens a new unit, else None."""
    if CHAPTER_RE.match(line):
        return ("chapter", None, line[:90])
    if DEFS_RE.match(line):
        return ("definitions", None, line[:90])
    m = NUM_HEADING_RE.match(line)
    if m:
        return ("section", m.group(1), line[:90])
    m = WORD_HEADING_RE.match(line)
    if m:
        return ("section", m.group(1), line[:90])
    return None



def split_sections(act: str, text: str, page_of, default_page: int = 1) -> list[Section]:
    """Split into sections. `page_of` maps a character offset to a page number."""
    out: list[Section] = []
    lines = text.split("\n")
    cur: Section | None = None
    offset = 0

    def flush():
        nonlocal cur
        if cur and cur.text.strip():
            cur.text = cur.text.strip()
            out.append(cur)
        cur = None

    for line in lines:
        stripped = line.strip()
        page = page_of(offset)
        head = _heading_of(stripped)
        if head:
            flush()
            kind, sec_no, title = head
            cur = Section(act=act, kind=kind, section_no=sec_no, title=title,
                          page_start=page, page_end=page)
        elif cur is None:
            cur = Section(act=act, kind="preamble", page_start=page, page_end=page)
        if cur is not None:
            cur.text += line + "\n"
            cur.page_end = page
        offset += len(line) + 1

    flush()
    return out
