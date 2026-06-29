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

        # Valid phone numbers usually contain at least 8 digits
        if len(digits_only) >= 8:
            return match.strip()

    return "Not Found"


# =====================================================
# NAME EXTRACTION
# =====================================================
def extract_name(text):

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

    # Expanded: covers section headings AND label prefixes found in resumes
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
        "career objective",       # ← was being picked as name
        "objective",
        "career summary",
        "professional profile",
        "personal statement",
        "about me",
        "technical skills",
        "soft skills",
        "core competencies",
        "key skills",
        "certifications",
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
        "name",
        "phone",
        "email",
        "mobile",
        "address",
        "linkedin",
        "github",
        "date of birth",
        "nationality",
        "marital status",
    ]

    lines = text.split('\n')

    for line in lines[:20]:

        line = line.strip()

        if not line:
            continue

        lower_line = line.lower()

        # Skip if the line IS a known heading (exact match)
        if lower_line in HEADINGS:
            continue

        # Skip if the line CONTAINS a known heading (e.g. "Career Objective")
        if any(heading in lower_line for heading in HEADINGS):
            continue

        # Skip common job titles
        if lower_line in JOB_TITLES:
            continue

        words = line.split()

        # Name usually 2-4 words
        if not (2 <= len(words) <= 4):
            continue

        # Ignore lines containing digits
        if any(char.isdigit() for char in line):
            continue

        # Ignore emails
        if '@' in line:
            continue

        # Skip lines that look like "Label: Value" (e.g. "Name: Elakiya V")
        if ':' in line:
            # Try extracting value after the colon as the name
            after_colon = line.split(':', 1)[1].strip()
            after_words = after_colon.split()
            if (
                1 <= len(after_words) <= 4
                and all(word.replace('.', '').isalpha() for word in after_words)
                and after_colon.lower() not in HEADINGS
            ):
                return after_colon.title()
            continue

        # All words alphabetic
        if all(word.replace('.', '').isalpha() for word in words):
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

    # Look for year ranges in experience sections (e.g. 2020-2023 → 3 years)
    # This helps when the resume lists job durations without saying "X years"
    year_range_pattern = r'(20\d{2})\s*[-–to]+\s*(20\d{2}|present|current)'
    ranges = re.findall(year_range_pattern, text_lower)
    total_years = 0
    for start, end in ranges:
        try:
            start_yr = int(start)
            end_yr = 2025 if end in ('present', 'current') else int(end)
            total_years += max(0, end_yr - start_yr)
        except ValueError:
            pass
    if total_years > 0:
        return f"{total_years} Years"

    # Fall back to explicit "X years" pattern
    pattern = r'(\d+)\+?\s*years?'
    matches = re.findall(pattern, text_lower)
    if matches:
        max_exp = max([int(x) for x in matches])
        return f"{max_exp} Years"

    # If education dates exist but no work history found, likely a fresher
    edu_keywords = ['b.com', 'bsc', 'btech', 'be ', 'msc', 'mba', 'bachelor', 'master', 'degree']
    has_education = any(kw in text_lower for kw in edu_keywords)
    work_keywords = ['worked at', 'employed', 'company', 'organisation', 'organization', 'pvt ltd', 'inc.', 'llc']
    has_work = any(kw in text_lower for kw in work_keywords)

    if has_education and not has_work:
        return "Fresher"

    return "Not Found"