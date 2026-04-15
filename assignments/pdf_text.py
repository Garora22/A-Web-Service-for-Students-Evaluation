"""Extract plain text from uploaded PDF files for MCQ generation."""

from io import BytesIO
from typing import BinaryIO


def extract_text_from_pdf(file_obj: BinaryIO) -> str:
    """
    Read PDF bytes from a file-like object and return concatenated page text.
    Raises RuntimeError if pypdf is not installed.
    Raises ValueError if no text could be extracted.
    """
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - env dependent
        raise RuntimeError(
            "PDF support requires 'pypdf'. Install with: pip install pypdf"
        ) from exc

    raw = file_obj.read()
    if hasattr(file_obj, "seek"):
        file_obj.seek(0)

    reader = PdfReader(BytesIO(raw))
    parts: list[str] = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            parts.append(text.strip())

    return "\n\n".join(parts)


def chunk_text(text: str, max_size: int = 4500, max_chunks: int = 10) -> list[str]:
    """Split long text into bounded chunks for LLM context limits."""
    text = text.strip()
    if not text:
        return []
    chunks: list[str] = []
    i = 0
    while i < len(text) and len(chunks) < max_chunks:
        chunks.append(text[i : i + max_size])
        i += max_size
    return chunks
