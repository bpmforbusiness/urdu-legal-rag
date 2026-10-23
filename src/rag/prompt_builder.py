"""Answer prompt for Urdu legal Q&A. Citation is mandatory."""
SYSTEM = (
    "آپ پاکستانی/بھارتی مرکزی قوانین کے اردو تراجم پر مبنی معاون ہیں۔ "
    "صرف دیے گئے اقتباسات کی بنیاد پر جواب دیں۔ اگر جواب اقتباسات میں نہ ہو تو صاف کہہ دیں کہ "
    "دیے گئے دستاویزات میں یہ معلومات موجود نہیں۔ کوئی بات خود سے نہ بنائیں۔ "
    "ہر جواب کے ساتھ متعلقہ دفعہ اور صفحہ نمبر کا حوالہ ضرور دیں۔ جواب اردو میں ہو۔"
)


def build_context(hits) -> str:
    blocks = []
    for i, (chunk, score) in enumerate(hits, start=1):
        head = f"[{i}] {chunk['act']}"
        if chunk.get("section_no"):
            head += f" — دفعہ {chunk['section_no']}"
        head += f" (صفحہ {chunk.get('page_start')})"
        blocks.append(f"{head}\n{chunk['text']}")
    return "\n\n---\n\n".join(blocks)


def build_messages(question: str, hits) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": f"اقتباسات:\n\n{build_context(hits)}\n\n"
                                    f"سوال: {question}"},
    ]
