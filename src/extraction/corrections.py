"""Context-aware OCR post-correction for known Urdu confusion pairs.

The vision model confuses a small set of visually similar Urdu letters. A naive
character-level dictionary is DANGEROUS here — for example "جج" is a real Urdu word
(judge), so a blanket د/ج fix would corrupt correct text. Every rule below is therefore
phrase-level and reversible, and every change is logged for audit.
"""
import re

# (pattern, replacement, reason). Patterns are anchored on phrases, not letters.
RULES: list[tuple[str, str, str]] = [
    (r"\bجج\s+کمیٹی", "حج کمیٹی", "ح/ج confusion on 'Haj Committee'"),
    (r"\bحج\s+سمیتی", "حج کمیٹی", "م/می confusion on 'Committee'"),
    (r"\bفدفہ\b", "دفعہ", "د/ف confusion on 'section'"),
    (r"\bدفعھ\b", "دفعہ", "heh variant of 'section'"),
    (r"\bدفعئ\b", "دفعہ", "hamza variant of 'section'"),
    (r"\bضمن\s*\(\s*(\d+)\s*\)", r"ضمن (\1)", "clause marker spacing"),
    (r"\bایکٹ\s+،", "ایکٹ،", "space before comma"),
    (r"\s+۔", "۔", "space before full stop"),
]


def apply_corrections(text: str) -> tuple[str, list[dict]]:
    """Return (corrected_text, changes). Never silent: every change is recorded."""
    changes: list[dict] = []
    out = text
    for pattern, repl, why in RULES:
        new, n = re.subn(pattern, repl, out)
        if n:
            changes.append({"pattern": pattern, "replacement": repl, "count": n, "why": why})
            out = new
    return out, changes


def summarize(changes: list[dict]) -> str:
    if not changes:
        return "no corrections"
    return "; ".join(f"{c['count']}x {c['why']}" for c in changes)
