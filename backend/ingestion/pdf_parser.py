import fitz  # PyMuPDF
from pathlib import Path
from typing import Optional
import re


def _clean_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\x20-\x7E\n]', '', text)
    return text.strip()


def parse_pdf(file_path: str) -> list[dict]:
    """Extract text chunks from a PDF with page-level provenance."""
    doc = fitz.open(file_path)
    chunks = []
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text("text")
        text = _clean_text(text)
        if not text:
            continue
        chunks.append({
            "text": text,
            "page_number": page_num,
            "total_pages": len(doc),
        })
    doc.close()
    return chunks


def parse_text_file(file_path: str) -> list[dict]:
    """Parse plain text files as single-page chunks."""
    text = Path(file_path).read_text(encoding="utf-8", errors="ignore")
    text = _clean_text(text)
    if not text:
        return []
    return [{"text": text, "page_number": 1, "total_pages": 1}]


def split_into_chunks(pages: list[dict], chunk_size: int = 800, overlap: int = 100) -> list[dict]:
    """Split page texts into overlapping chunks, preserving page provenance."""
    chunks = []
    for page in pages:
        text = page["text"]
        words = text.split()
        start = 0
        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunk_text = " ".join(words[start:end])
            chunks.append({
                "text": chunk_text,
                "page_number": page["page_number"],
                "total_pages": page["total_pages"],
            })
            if end == len(words):
                break
            start = end - overlap
    return chunks


def parse_document(file_path: str, chunk_size: int = 800, overlap: int = 100) -> list[dict]:
    """Unified entry point: parse any supported file into overlapping chunks."""
    path = Path(file_path)
    if path.suffix.lower() == ".pdf":
        pages = parse_pdf(file_path)
    else:
        pages = parse_text_file(file_path)
    return split_into_chunks(pages, chunk_size, overlap)
