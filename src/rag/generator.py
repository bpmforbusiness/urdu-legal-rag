"""LLM answer generation over retrieved context (OpenAI-compatible)."""
import json
import os
import urllib.request

from src.extraction.ocr import _env
from src.rag.prompt_builder import build_messages


class Generator:
    def __init__(self, base_url: str | None = None, api_key: str | None = None,
                 model: str | None = None):
        self.base_url = base_url or _env("LLM_BASE_URL",
                                        "https://opencode.ai/zen/go/v1/chat/completions")
        self.api_key = api_key or _env("LLM_API_KEY") or _env("OPENCODE_GO_API_KEY")
        self.model = model or _env("LLM_MODEL", "deepseek-v4-flash")

    def answer(self, question: str, hits, timeout: int = 120) -> str:
        payload = {"model": self.model, "messages": build_messages(question, hits),
                   "temperature": 0}
        headers = {"Content-Type": "application/json",
                   "Authorization": f"Bearer {self.api_key}",
                   "User-Agent": _env("OCR_USER_AGENT", "hermes")}
        hdr, val = _env("OCR_SESSION_HEADER", ""), _env("OCR_SESSION_VALUE", "")
        if hdr and val:
            headers[hdr] = val
        req = urllib.request.Request(self.base_url, data=json.dumps(payload).encode(),
                                     headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode())
        return (body.get("choices", [{}])[0].get("message", {}).get("content") or "").strip()
