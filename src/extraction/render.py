"""PDF -> page PNGs. No text extraction: this corpus has no usable text layer."""
import os

import pymupdf as fitz


def render_pages(pdf_path: str, out_dir: str, dpi: int = 200,
                 first: int = 1, last: int | None = None) -> list[str]:
    """Render pages [first, last] to PNG. Returns the file paths."""
    os.makedirs(out_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    last = min(last or doc.page_count, doc.page_count)
    paths = []
    for i in range(first - 1, last):
        dest = os.path.join(out_dir, f"page-{i + 1:04d}.png")
        if not os.path.exists(dest):
            doc[i].get_pixmap(dpi=dpi).save(dest)
        paths.append(dest)
    doc.close()
    return paths


def page_count(pdf_path: str) -> int:
    doc = fitz.open(pdf_path)
    n = doc.page_count
    doc.close()
    return n
