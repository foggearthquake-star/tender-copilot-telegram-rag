from __future__ import annotations

import io
import re
from pathlib import Path

from docx import Document
from pypdf import PdfReader

from app.core.config import settings


class ParseResult:
    def __init__(self, doc_name: str, text: str, is_empty: bool = False, used_ocr: bool = False) -> None:
        self.doc_name = doc_name
        self.text = text
        self.is_empty = is_empty
        self.used_ocr = used_ocr


def parse_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def ocr_pdf(path: Path) -> str:
    try:
        import fitz
        import pytesseract
        from PIL import Image
    except Exception:
        return ""

    if settings.tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd

    try:
        doc = fitz.open(str(path))
    except Exception:
        return ""

    texts: list[str] = []
    for page in doc:
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        image = Image.open(io.BytesIO(pix.tobytes("png")))
        text = pytesseract.image_to_string(image, lang="rus+eng")
        if text.strip():
            texts.append(text)
    return "\n".join(texts)


def parse_docx(path: Path) -> str:
    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def parse_document(path: Path) -> ParseResult:
    suffix = path.suffix.lower()
    used_ocr = False
    if suffix == ".pdf":
        text = parse_pdf(path)
        if settings.enable_ocr and not text.strip():
            text = ocr_pdf(path)
            used_ocr = bool(text.strip())
    elif suffix == ".docx":
        text = parse_docx(path)
    else:
        raise ValueError(f"Unsupported extension: {suffix}")

    is_empty = not bool(text.strip())
    text = re.sub(r"\s+", " ", text).strip()
    return ParseResult(doc_name=path.name, text=text, is_empty=is_empty, used_ocr=used_ocr)


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 120) -> list[str]:
    if not text.strip():
        return []
    if len(text) <= chunk_size:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = max(0, end - overlap)
    return chunks
