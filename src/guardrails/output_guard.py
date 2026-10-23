"""Answer guardrails: must be Urdu, must cite at least one retrieved source."""
from src.extraction.normalize import arabic_ratio

MIN_ANSWER_CHARS = 20


def check(answer: str, hits) -> tuple[bool, list[str]]:
    problems = []
    a = (answer or "").strip()
    if len(a) < MIN_ANSWER_CHARS:
        problems.append("answer too short")
    if arabic_ratio(a) < 0.4:
        problems.append("answer is not predominantly in Urdu")
    if hits and not any(str(c.get("section_no") or "") in a or
                        c["act"].replace("-", " ")[:18] in a for c, _ in hits):
        problems.append("answer cites no retrieved source")
    return (not problems), problems
