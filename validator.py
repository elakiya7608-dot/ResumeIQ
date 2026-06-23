"""
validator.py — Resume Validator for ResumeIQ
Validates whether an uploaded document is a genuine resume/CV before analysis.

Text extraction is delegated to the same functions used by app.py
(resume.py + ocr_helper.py) so the validator never disagrees with the
main pipeline about whether a file is readable.
"""

import re
import io
import os
import tempfile
from typing import Tuple

from resume import extract_text_from_pdf,extract_text_from_docx
from ocr_helper import extract_text_from_scanned_pdf, extract_text_from_docx_images


# ---------------------------------------------------------------------------
# RESUME keywords — document must contain enough of these to pass
# ---------------------------------------------------------------------------
RESUME_KEYWORDS = [
    # ── Identity / Contact ──────────────────────────────────────────────────
    "email", "phone", "mobile", "linkedin", "github",
    "portfolio", "nationality", "date of birth", "dob",
    "marital status",

    # ── Resume / CV document markers ────────────────────────────────────────
    "resume", "curriculum vitae",

    # ── Profile / Objective section headings ────────────────────────────────
    "career objective","summary","profile","professional summary", "personal statement",
    "about me", "career summary", "professional profile",

    # ── Work Experience section headings ────────────────────────────────────
    "work experience", "professional experience","experience"
    "employment history", "work history", "career history",
    "internship", "job title", "designation",
    "key contributions", "full-time", "part-time", "freelance",

    # ── Education section headings ───────────────────────────────────────────
    "educational qualification", "academic background",
    "bachelor", "master", "phd", "doctorate", "diploma",
    "graduated", "graduation", "gpa", "cgpa",
    "coursework", "thesis", "dissertation",

    # ── Skills section headings ──────────────────────────────────────────────
    "technical skills", "soft skills", "core competencies",
    "key skills", "areas of expertise",
    "proficiencies", "programming languages", "languages known",

    # ── Certifications / Training ────────────────────────────────────────────
    "certifications", "certified", "bootcamp",
    "online courses", "professional develpment",
    "accreditation", "licensure",

    # ── Projects ─────────────────────────────────────────────────────────────
    "personal projects", "academic projects","projects",
    "capstone project", "open source",

    # ── Awards / Honours ─────────────────────────────────────────────────────
    "awards", "honours", "honors", "scholarship",
    "fellowship", "distinction", "dean's list",

    # ── Publications / Research ──────────────────────────────────────────────
    "publications", "presented at", "authored",

    # ── Volunteering / Extra-curricular ──────────────────────────────────────
    "volunteering", "community service",
    "extracurricular", "team lead",

    # ── References ───────────────────────────────────────────────────────────
    "referees", "available upon request",

    # ── Languages ────────────────────────────────────────────────────────────
    "fluent", "bilingual", "languages known",

    # ── Hobbies / Interests ──────────────────────────────────────────────────
    "hobbies", "passions",

    # ── Declarations ─────────────────────────────────────────────────────────
    "i hereby declare", "i certify that",
]

# ---------------------------------------------------------------------------
# HARD-BLOCK phrases — reject immediately if found
# ---------------------------------------------------------------------------
HARD_BLOCK_PHRASES = [
    " business",
    "sbr service desk",
    "taxpayer declaration",
    "tax return",
    "abn registration",
    "business activity statement",
    "goods and services tax",
    "common business implementation",
    "online services for dsps",
    "terms and conditions",
    "privacy policies",
    "memorandum of understanding",
    "this document and its attachments are official",
    "for further information raise an enquiry",
    "balance sheet",
    "profit and loss",
    "income statement",
    "annual report",
    "financial statement",
    "purchase order",
    "patient diagnosis",
    "prescription",
    "doi:",
    "issn:",
    "literature review",
    "user manual",
    "instruction manual",
    "policy document",
    "implementation guide",
    "meeting minutess",
]

# Thresholds
MIN_RESUME_KEYWORD_HITS = 3
MIN_TEXT_LENGTH         = 100
MAX_TEXT_LENGTH         = 50_000

# ---------------------------------------------------------------------------
# Reason codes — used by app.py to decide how to handle each rejection
# ---------------------------------------------------------------------------
REASON_EMPTY        = "empty"          # blank / unreadable — route to AI
REASON_TOO_LONG     = "too_long"       # definitely not a resume — hard reject
REASON_HARD_BLOCK   = "hard_block"     # official/legal doc — hard reject
REASON_NOT_RESUME   = "not_resume"     # low keyword count — route to AI


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------

def _extract_text(file_bytes: bytes, filename: str) -> str:
    text = ""
    ext = filename.lower().rsplit(".", 1)[-1]
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix="." + ext) as tmp:
            tmp.write(file_bytes)
            temp_path = tmp.name

        if ext == "pdf":
            try:
                text = extract_text_from_pdf(io.BytesIO(file_bytes))
            except Exception:
                text = ""
            if not text.strip():
                try:
                    text = extract_text_from_scanned_pdf(temp_path)
                except Exception:
                    text = ""

        elif ext in ("docx", "doc"):
            try:
                text = extract_text_from_docx(io.BytesIO(file_bytes))
            except Exception:
                text = ""
            if not text.strip():
                try:
                    text = extract_text_from_docx_images(temp_path)
                except Exception:
                    text = ""

    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass

    return text


# ---------------------------------------------------------------------------
# Core validation helpers
# ---------------------------------------------------------------------------

def _check_hard_block(text_lower: str):
    for phrase in HARD_BLOCK_PHRASES:
        if phrase in text_lower:
            return phrase
    return None


def _count_resume_keyword_hits(text_lower: str) -> Tuple[int, list]:
    hits = []
    for kw in RESUME_KEYWORDS:
        pattern = r'\b' + re.escape(kw) + r'\b'
        if re.search(pattern, text_lower):
            hits.append(kw)
    return len(hits), hits


def _has_contact_info(text_lower: str) -> bool:
    email_pattern = r'[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}'
    phone_pattern = r'(\+?\d[\d\s\-().]{7,}\d)'
    return bool(
        re.search(email_pattern, text_lower) or
        re.search(phone_pattern, text_lower)
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_resume(file_bytes: bytes, filename: str) -> Tuple[bool, str, dict]:
    """
    Validate whether the uploaded document is a genuine resume/CV.

    Returns
    -------
    is_valid : bool
    message  : str   — shown to user on rejection
    details  : dict  — includes "reason" key so app.py can route correctly:
                         "empty"      → pass to AI for polite response
                         "not_resume" → pass to AI for polite response
                         "too_long"   → hard reject (not a resume)
                         "hard_block" → hard reject (official/legal doc)
    """

    text       = _extract_text(file_bytes, filename)
    text_lower = text.lower().strip()

    details = {
        "filename":              filename,
        "text_length":           len(text_lower),
        "resume_keywords_found": [],
        "has_contact_info":      False,
        "blocked_by":            None,
        "reason":                None,          # ← NEW: always set on rejection
    }

    # --- 1. Empty / unreadable → let AI respond politely ---
    if len(text_lower) < MIN_TEXT_LENGTH:
        details["reason"] = REASON_EMPTY
        return (
            False,
            "The uploaded document appears to be empty or could not be read.",
            details,
        )

    # --- 2. Too long to be a resume → hard reject ---
    if len(text_lower) > MAX_TEXT_LENGTH:
        details["reason"] = REASON_TOO_LONG
        return (
            False,
            "❌ The uploaded document is too long to be a resume. "
            "Resumes are typically 1–3 pages. Please upload the correct file.",
            details,
        )

    # --- 3. Hard-block: official / legal / government doc → hard reject ---
    blocked_phrase = _check_hard_block(text_lower)
    if blocked_phrase:
        details["blocked_by"] = blocked_phrase
        details["reason"]     = REASON_HARD_BLOCK
        return (
            False,
            "❌ This document does not appear to be a resume. "
            "It looks like an official, legal, or government document. "
            "Please upload your personal resume or CV in PDF or DOCX format.",
            details,
        )

    # --- 4. Too few resume keywords → let AI respond politely ---
    resume_hits, resume_found = _count_resume_keyword_hits(text_lower)
    details["resume_keywords_found"] = resume_found

    if resume_hits < MIN_RESUME_KEYWORD_HITS:
        details["reason"] = REASON_NOT_RESUME
        return (
            False,
            f"The document does not appear to be a resume "
            f"({resume_hits} resume keyword(s) detected; "
            f"minimum required: {MIN_RESUME_KEYWORD_HITS}).",
            details,
        )

    # --- 5. All checks passed ---
    has_contact            = _has_contact_info(text_lower)
    details["has_contact_info"] = has_contact

    return (
        True,
        f"✅ Document validated as a resume ({resume_hits} resume keyword(s) detected).",
        details,
    )
