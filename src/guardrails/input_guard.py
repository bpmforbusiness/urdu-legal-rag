"""Reject inputs that are not answerable questions in Urdu/Arabic script."""
from src.extraction.normalize import arabic_ratio

MAX_QUESTION_CHARS = 500


def check(question: str) -> tuple[bool, str]:
    q = (question or "").strip()
    if not q:
        return False, "empty question"
    if len(q) > MAX_QUESTION_CHARS:
        return False, f"question too long ({len(q)} chars, max {MAX_QUESTION_CHARS})"
    if arabic_ratio(q) < 0.4:
        return False, "question is not predominantly in Urdu/Arabic script"
    return True, ""
