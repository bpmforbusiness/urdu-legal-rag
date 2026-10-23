"""Data models with page-level provenance."""
from typing import Optional

from pydantic import BaseModel, Field


class PageOCR(BaseModel):
    """One rendered page of one act, as transcribed."""

    act: str
    page: int = Field(ge=1)
    text: str
    ocr_model: str
    ocr_sha: str
    dpi: int
    chars: int = 0
    arabic_ratio: float = 0.0

    def model_post_init(self, _ctx) -> None:
        if not self.chars:
            self.chars = len(self.text)
        if not self.arabic_ratio:
            total = arabic = 0
            for ch in self.text:
                if ch.isalpha():
                    total += 1
                    if "\u0600" <= ch <= "\u06ff":
                        arabic += 1
            self.arabic_ratio = round(arabic / total, 4) if total else 0.0


class Section(BaseModel):
    """A section (دفعہ) or chapter heading, with where it came from."""

    act: str
    section_no: Optional[str] = None
    title: Optional[str] = None
    kind: str = "section"           # chapter | section | definitions | preamble
    text: str = ""
    page_start: int = 1
    page_end: int = 1


class ExtractedAct(BaseModel):
    act: str
    pdf: str
    pages: int
    pages_ocred: int
    sections: list[Section] = []
    warnings: list[str] = []
