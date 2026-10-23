"""Vision-model OCR for pages with no usable text layer.

Cached per (pdf content hash, page, model, max_px) so a re-run costs nothing.
"""
import base64
import hashlib
import json
import os
import random
import time
import urllib.error
import urllib.request

DEFAULT_PROMPT = (
    "This is a page from an Indian central act translated into Urdu. "
    "Transcribe ALL text on the page verbatim in Urdu. Preserve the numbering of sections "
    "(دفعہ), sub-sections ((1), (2)), and clause letters ((الف), (ب), (ج), (د)), and keep "
    "chapter headings (باب). Output only the transcription, no commentary, no translation. "
    "If a word is unreadable, write [??] for it rather than guessing."
)


class OcrError(RuntimeError):
    pass


def _env(key: str, default: str = "") -> str:
    val = os.environ.get(key)
    if val:
        return val
    # project-local .env first, then the Hermes-wide one
    for path in (os.path.expanduser("~/urdu_rag/.env"),
                 os.path.expanduser("~/.hermes/.env")):
        if os.path.exists(path):
            for line in open(path):
                line = line.strip()
                if line.startswith(key + "="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return default


def _b64(path: str, max_px: int) -> str:
    from PIL import Image
    im = Image.open(path).convert("RGB")
    if max(im.size) > max_px:
        im.thumbnail((max_px, max_px))
        tmp = f"/tmp/ocr_small_{os.getpid()}.jpg"
        im.save(tmp, "JPEG", quality=90)
        path = tmp
    return base64.b64encode(open(path, "rb").read()).decode()


class OcrClient:
    """OpenAI-compatible chat-completions vision OCR."""

    def __init__(self, base_url: str | None = None, api_key: str | None = None,
                 model: str | None = None, max_px: int | None = None,
                 cache_dir: str | None = None, prompt: str | None = None):
        self.base_url = base_url or _env("OCR_BASE_URL",
                                        "https://opencode.ai/zen/go/v1/chat/completions")
        self.api_key = api_key or _env("OCR_API_KEY") or _env("OPENCODE_GO_API_KEY")
        self.model = model or _env("OCR_MODEL", "deepseek-v4-flash-vision-exp")
        self.max_px = int(max_px or _env("OCR_MAX_PX", "1600"))
        self.cache_dir = os.path.expanduser(
            cache_dir or _env("OCR_CACHE_DIR", "data/ocr_cache"))
        self.prompt = prompt or DEFAULT_PROMPT
        self.session_hdr = _env("OCR_SESSION_HEADER", "")
        self.session_val = _env("OCR_SESSION_VALUE", "")
        os.makedirs(self.cache_dir, exist_ok=True)

    def cache_key(self, image_path: str, page: int) -> str:
        digest = hashlib.sha256(open(image_path, "rb").read()).hexdigest()[:24]
        raw = f"{digest}|{page}|{self.model}|{self.max_px}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def transcribe(self, image_path: str, page: int, retries: int = 4) -> dict:
        key = self.cache_key(image_path, page)
        cached = os.path.join(self.cache_dir, key + ".json")
        if os.path.exists(cached):
            rec = json.load(open(cached))
            rec["cached"] = True
            return rec
        if not self.api_key:
            raise OcrError("no OCR_API_KEY configured")

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": self.prompt},
                {"type": "image_url",
                 "image_url": {"url": "data:image/jpeg;base64," + _b64(image_path, self.max_px)}},
            ]}],
            "temperature": 0,
        }
        headers = {"Content-Type": "application/json",
                   "Authorization": f"Bearer {self.api_key}",
                   # Cloudflare fronts this endpoint and returns HTTP 403 code 1010 to
                   # Python-urllib's default User-Agent, so a UA is mandatory.
                   "User-Agent": _env("OCR_USER_AGENT", "hermes")}
        if self.session_hdr and self.session_val:
            headers[self.session_hdr] = self.session_val

        last = ""
        for attempt in range(1, retries + 1):
            try:
                req = urllib.request.Request(self.base_url, data=json.dumps(payload).encode(),
                                             headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=180) as resp:
                    body = json.loads(resp.read().decode())
                text = (body.get("choices", [{}])[0].get("message", {}).get("content") or "").strip()
                if text:
                    rec = {"page": page, "text": text, "model": self.model,
                           "key": key, "cached": False}
                    json.dump(rec, open(cached, "w"), ensure_ascii=False, indent=1)
                    return rec
                last = "empty content"
            except urllib.error.HTTPError as exc:
                last = f"HTTP {exc.code}: {exc.read()[:200].decode(errors='replace')}"
            except Exception as exc:                                    # noqa: BLE001
                last = f"{type(exc).__name__}: {exc}"
            time.sleep(min(2 ** attempt, 15) + random.random())
        raise OcrError(f"page {page}: {retries} attempts failed — {last}")
