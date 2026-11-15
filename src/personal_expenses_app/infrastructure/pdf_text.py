"""PDF text extraction, kept apart from statement parsing.

Extracting text with pdfplumber is CPU-bound and takes about 90% of an import, so it lives
in its own dependency-light module: worker processes can import it cheaply, and the bank
parsers can be exercised with plain strings instead of PDFs.
"""

from __future__ import annotations

import io

import pdfplumber


def extract_page_texts(pdf_bytes: bytes) -> list[str]:
    """Return the text of every page of a PDF, in order ("" for a page without text)."""
    page_texts = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_texts.append(page.extract_text() or "")
            page.close()  # Drop the page's cached layout objects; they dwarf the text.
    return page_texts
