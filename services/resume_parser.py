"""
services/resume_parser.py
--------------------------
Extracts raw text from uploaded resume files (PDF or DOCX).

Supported formats
-----------------
.pdf  → pdfplumber
.docx → python-docx
"""

import os
import re
import pdfplumber
from docx import Document


def extract_text_from_pdf(filepath: str) -> str:
    """
    Extract all text from a PDF file using pdfplumber.

    Parameters
    ----------
    filepath : absolute path to the .pdf file

    Returns
    -------
    str : concatenated text from all pages
    """
    text_parts = []
    try:
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
    except Exception as e:
        raise ValueError(f"Failed to read PDF '{filepath}': {e}")

    return "\n".join(text_parts)


def extract_text_from_docx(filepath: str) -> str:
    """
    Extract all paragraph text from a DOCX file.

    Parameters
    ----------
    filepath : absolute path to the .docx file

    Returns
    -------
    str : concatenated paragraph text
    """
    try:
        doc = Document(filepath)
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        return "\n".join(paragraphs)
    except Exception as e:
        raise ValueError(f"Failed to read DOCX '{filepath}': {e}")


def extract_resume_text(filepath: str) -> str:
    """
    Route to the correct extractor based on file extension.

    Parameters
    ----------
    filepath : absolute path to the uploaded resume

    Returns
    -------
    str : raw extracted text
    """
    ext = os.path.splitext(filepath)[-1].lower()

    if ext == ".pdf":
        return extract_text_from_pdf(filepath)
    elif ext in (".docx", ".doc"):
        return extract_text_from_docx(filepath)
    else:
        raise ValueError(f"Unsupported file format: '{ext}'")


# ── Lightweight field heuristics ──────────────────────────────────────────────
# These are best-effort patterns — a full NER pipeline is overkill for a
# final-year project, but these cover common resume layouts.

def extract_email(text: str) -> str:
    match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    return match.group(0) if match else ""


def extract_phone(text: str) -> str:
    # Handles formats like +91-9876543210, (123) 456-7890, 9876543210
    match = re.search(
        r"(\+?\d[\d\s\-().]{8,15}\d)", text
    )
    return match.group(0).strip() if match else ""


def parse_resume_fields(raw_text: str) -> dict:
    """
    Extract structured fields from raw resume text.

    Returns
    -------
    dict with keys: email, phone
    (name extraction is left to the upload form for accuracy)
    """
    return {
        "email": extract_email(raw_text),
        "phone": extract_phone(raw_text),
    }
