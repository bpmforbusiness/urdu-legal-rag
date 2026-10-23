"""Sections -> retrieval chunks, keeping act/section/page provenance."""
import hashlib

MAX_CHARS = 800
MIN_CHARS = 120
OVERLAP = 120


def chunk_id(act: str, section_no: str | None, page: int, idx: int) -> str:
    raw = f"{act}|{section_no or 'x'}|{page}|{idx}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def split_long(text: str, max_chars: int = MAX_CHARS, overlap: int = OVERLAP) -> list[str]:
    """Split on line boundaries where possible so clauses stay intact.

    A single line longer than max_chars (OCR sometimes returns a whole page as one line)
    is hard-split, otherwise it would pass through un-split.
    """
    if len(text) <= max_chars:
        return [text] if text.strip() else []

    parts: list[str] = []
    cur = ""

    def flush():
        nonlocal cur
        if cur.strip():
            parts.append(cur.strip())
        cur = ""

    for line in text.split("\n"):
        if len(line) > max_chars:
            flush()
            step = max(1, max_chars - overlap)
            parts.extend(line[i:i + max_chars] for i in range(0, len(line), step))
            continue
        if len(cur) + len(line) + 1 <= max_chars:
            cur += line + "\n"
        else:
            tail = cur[-overlap:] if overlap and cur else ""
            flush()
            cur = (tail + "\n" + line + "\n") if tail else line + "\n"
    flush()
    return parts


def chunks_from_act(act_json: dict) -> list[dict]:
    """Every chunk keeps act, section number/title, and page range — for citation."""
    act = act_json["act"]
    out = []
    for section in act_json.get("sections", []):
        text = (section.get("text") or "").strip()
        if len(text) < MIN_CHARS and section.get("kind") != "definitions":
            if text:
                text = text  # keep short headings; they carry navigation value
            else:
                continue
        for idx, piece in enumerate(split_long(text)):
            out.append({
                "chunk_id": chunk_id(act, section.get("section_no"), section.get("page_start", 1), idx),
                "act": act,
                "kind": section.get("kind"),
                "section_no": section.get("section_no"),
                "section_title": section.get("title"),
                "page_start": section.get("page_start"),
                "page_end": section.get("page_end"),
                "text": piece,
                "chars": len(piece),
            })
    return out


def citation(chunk: dict) -> str:
    """Human-readable citation, e.g. 'حج کمیٹی ایکٹ 2002، دفعہ 3، ص 2'."""
    bits = [chunk["act"].replace("-", " ")]
    if chunk.get("section_no"):
        bits.append(f"section {chunk['section_no']}")
    if chunk.get("page_start"):
        bits.append(f"p{chunk['page_start']}")
    return ", ".join(bits)
