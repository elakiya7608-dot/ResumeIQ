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

from resume import extract_text_from_pdf, extract_text_from_docx
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
    "career objective", "summary", "profile", "professional summary", "personal statement",
    "about me", "career summary", "professional profile",

    # ── Work Experience section headings ────────────────────────────────────
    "work experience", "professional experience", "experience",
    "employment history", "work history", "career history",
    "internship", "job title", "designation",
    "key contributions", "full-time", "part-time", "freelance",

    # ── Education section headings ───────────────────────────────────────────
    "educational qualification", "academic background", "qualification",
    "bachelor", "master", "phd", "doctorate", "diploma",
    "graduated", "graduation", "gpa", "cgpa",
    "coursework", "thesis", "dissertation",

    # ── Skills section headings ──────────────────────────────────────────────
    "technical skills", "soft skills", "core competencies",
    "key skills", "areas of expertise",
    "proficiencies", "programming languages", "languages known",

    # ── Certifications / Training ────────────────────────────────────────────
    "certifications", "certified", "bootcamp",
    "online courses", "professional development",
    "accreditation", "licensure",

    # ── Projects ─────────────────────────────────────────────────────────────
    "personal projects", "academic projects", "projects",
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

# ── Education keywords for scoring ──────────────────────────────────────────
EDUCATION_KEYWORDS = [
    "bachelor", "master", "phd", "doctorate", "diploma",
    "graduated", "graduation", "gpa", "cgpa", "degree",
    "university", "college", "institute", "school",
    "educational qualification", "academic background",
    "coursework", "thesis", "dissertation",
]

# ── Skills keywords for scoring ─────────────────────────────────────────────
SKILLS_KEYWORDS = [
    "technical skills", "soft skills", "core competencies",
    "key skills", "areas of expertise", "proficiencies",
    "programming languages", "languages known", "skills",
    "tools", "technologies", "frameworks",
]

# Thresholds
MIN_RESUME_KEYWORD_HITS = 3
MIN_TEXT_LENGTH         = 100
MAX_TEXT_LENGTH         = 50_000
MIN_SCORE               = 4     # minimum score out of 8 to pass validation

# ---------------------------------------------------------------------------
# Reason codes — used by app.py to decide how to handle each rejection
# ---------------------------------------------------------------------------
REASON_EMPTY        = "empty"        # blank / unreadable — route to AI
REASON_TOO_LONG     = "too_long"     # definitely not a resume — hard reject
REASON_NOT_RESUME   = "not_resume"   # low keyword count or score — route to AI


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

def _count_resume_keyword_hits(text_lower: str) -> Tuple[int, list]:
    hits = []
    for kw in RESUME_KEYWORDS:
        pattern = r'\b' + re.escape(kw) + r'\b'
        if re.search(pattern, text_lower):
            hits.append(kw)
    return len(hits), hits


def _has_email(text_lower: str) -> bool:
    email_pattern = r'[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}'
    return bool(re.search(email_pattern, text_lower))


def _has_phone(text_lower: str) -> bool:
    phone_pattern = r'(\+?\d[\d\s\-().]{7,}\d)'
    return bool(re.search(phone_pattern, text_lower))


def _has_education(text_lower: str) -> bool:
    for kw in EDUCATION_KEYWORDS:
        pattern = r'\b' + re.escape(kw) + r'\b'
        if re.search(pattern, text_lower):
            return True
    return False


def _has_skills(text_lower: str) -> bool:
    for kw in SKILLS_KEYWORDS:
        pattern = r'\b' + re.escape(kw) + r'\b'
        if re.search(pattern, text_lower):
            return True
    return False


def _compute_score(text_lower: str) -> Tuple[int, dict]:
    """
    Score the document out of 8 based on presence of key resume signals:
      +2  email detected
      +2  phone detected
      +2  education section/keywords detected
      +2  skills section/keywords detected
    """
    score = 0
    breakdown = {
        "email":     False,
        "phone":     False,
        "education": False,
        "skills":    False,
    }

    if _has_email(text_lower):
        score += 2
        breakdown["email"] = True

    if _has_phone(text_lower):
        score += 2
        breakdown["phone"] = True

    if _has_education(text_lower):
        score += 2
        breakdown["education"] = True

    if _has_skills(text_lower):
        score += 2
        breakdown["skills"] = True

    return score, breakdown


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
    """

    text       = _extract_text(file_bytes, filename)
    text_lower = text.lower().strip()

    details = {
        "filename":              filename,
        "text_length":           len(text_lower),
        "resume_keywords_found": [],
        "score":                 0,
        "score_breakdown":       {},
        "reason":                None,
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

    # --- 3. Resume keyword check ---
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

    # --- 4. Scoring check: email, phone, education, skills ---
    score, score_breakdown = _compute_score(text_lower)
    details["score"]           = score
    details["score_breakdown"] = score_breakdown

    if score < MIN_SCORE:
        missing = [field for field, found in score_breakdown.items() if not found]
        details["reason"] = REASON_NOT_RESUME
        return (
            False,
            f"The document does not appear to be a resume. "
            f"Validation score: {score}/8 (minimum required: {MIN_SCORE}/8). "
            f"Missing sections: {', '.join(missing)}.",
            details,
        )

    # --- 5. All checks passed ---
    return (
        True,
        f"✅ Document validated as a resume "
        f"({resume_hits} resume keyword(s) detected, score: {score}/8).",
        details,
    )