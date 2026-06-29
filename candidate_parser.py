import re

# =====================================================
# EMAIL EXTRACTION
# =====================================================
def extract_email(text):

    pattern = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'

    match = re.search(pattern, text)

    if match:
        return match.group()

    return "Not Found"

# =====================================================
# PHONE EXTRACTION
# =====================================================
def extract_phone(text):

    pattern = r'[\+]?\d[\d\s\-\(\)]{7,20}\d'

    matches = re.findall(pattern, text)

    for match in matches:

        digits_only = ''.join(filter(str.isdigit, match))

        if len(digits_only) >= 8:
            return match.strip()

    return "Not Found"


# =====================================================
# NAME EXTRACTION
# =====================================================
def extract_name(text):

    # Label prefixes that directly contain the name after ":"
    # These are checked FIRST before any heading skip logic
    NAME_LABELS = [
        "name",
        "full name",
        "candidate name",
        "applicant name",
        "student name",
    ]

    JOB_TITLES = [
        "software engineer",
        "marketing manager",
        "data analyst",
        "business analyst",
        "project manager",
        "ai engineer",
        "machine learning engineer",
        "developer",
        "intern",
        "marketing executive",
        "manager",
        "professional summary",
    ]

    # Section headings to skip
    # NOTE: "name" is NOT here — handled separately via NAME_LABELS above
    HEADINGS = [
        "profile",
        "education",
        "skills",
        "contact",
        "experience",
        "work experience",
        "projects",
        "certifications",
        "summary",
        "resume",
        "curriculum vitae",
        "cv",
        "career objective",
        "objective",
        "career summary",
        "professional profile",
        "personal statement",
        "about me",
        "technical skills",
        "soft skills",
        "core competencies",
        "key skills",
        "achievements",
        "awards",
        "languages",
        "hobbies",
        "interests",
        "references",
        "declaration",
        "internship",
        "volunteering",
        "publications",
        "phone",
        "email",
        "mobile",
        "address",
        "linkedin",
        "github",
        "date of birth",
        "nationality",
        "marital status",
        "professional summary",
        "educational qualification",
        "work history",
        "employment history",
    ]

    lines = text.split('\n')

    for line in lines[:20]:

        line = line.strip()

        if not line:
            continue

        lower_line = line.lower()

        # ── PRIORITY CHECK: "Name: Elakiya V" style lines ──────────────────
        # Done BEFORE heading skip — "name" would otherwise match HEADINGS
        # and get skipped before we ever reach the colon logic.
        if ':' in line:
            label_part  = line.split(':', 1)[0].strip().lower()
            value_part  = line.split(':', 1)[1].strip()
            value_words = value_part.split()

            if (
                label_part in NAME_LABELS
                and 1 <= len(value_words) <= 4
                and not any(char.isdigit() for char in value_part)
                and '@' not in value_part
                and all(word.replace('.', '').replace('-', '').isalpha()
                        for word in value_words)
            ):
                return value_part.title()

            # Any other "Label: value" line that is not a name label → skip
            continue

        # ── Skip known section headings ──────────────────────────────────────
        if lower_line in HEADINGS:
            continue

        if any(heading in lower_line for heading in HEADINGS):
            continue

        # ── Skip known job titles ─────────────────────────────────────────────
        if lower_line in JOB_TITLES:
            continue

        words = line.split()

        # Names are 2–4 words long
        if not (2 <= len(words) <= 4):
            continue

        # No digits (rules out phone numbers, dates, years)
        if any(char.isdigit() for char in line):
            continue

        # No email addresses
        if '@' in line:
            continue

        # All words must be alphabetic (allows hyphenated names like "Mary-Jane")
        if all(word.replace('.', '').replace('-', '').isalpha() for word in words):
            return line.title()

    return "Not Found"


# =====================================================
# EXPERIENCE EXTRACTION
# =====================================================
def extract_experience(text):

    text_lower = text.lower()

    # Check for explicit fresher / entry-level indicators first
    fresher_patterns = [
        r'\bfresher\b',
        r'\bentry[- ]level\b',
        r'\bno experience\b',
        r'\b0 years?\b',
        r'\bzero years?\b',
    ]
    for fp in fresher_patterns:
        if re.search(fp, text_lower):
            return "Fresher"

    # Calculate from year ranges (e.g. "2020 - 2023" → 3 years)
    year_range_pattern = r'(20\d{2})\s*[-–to]+\s*(20\d{2}|present|current)'
    ranges = re.findall(year_range_pattern, text_lower)
    total_years = 0
    for start, end in ranges:
        try:
            start_yr = int(start)
            end_yr   = 2025 if end in ('present', 'current') else int(end)
            total_years += max(0, end_yr - start_yr)
        except ValueError:
            pass
    if total_years > 0:
        return f"{total_years} Years"

    # Fall back to explicit "X years" mention
    pattern = r'(\d+)\+?\s*years?'
    matches = re.findall(pattern, text_lower)
    if matches:
        max_exp = max([int(x) for x in matches])
        return f"{max_exp} Years"

    # Infer fresher from education-only resume
    edu_keywords  = ['b.com', 'bsc', 'btech', 'be ', 'msc', 'mba',
                     'bachelor', 'master', 'degree']
    work_keywords = ['worked at', 'employed', 'company', 'organisation',
                     'organization', 'pvt ltd', 'inc.', 'llc']

    has_education = any(kw in text_lower for kw in edu_keywords)
    has_work      = any(kw in text_lower for kw in work_keywords)

    if has_education and not has_work:
        return "Fresher"

    return "Not Found"