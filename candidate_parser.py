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
        "professional summary"
    ]

    HEADINGS = [
        "profile",
        "education",
        "skills",
        "contact",
        "experience",
        "work experience",
        "projects",
        "certifications",
        "summary"
    ]

    lines = text.split('\n')

    for line in lines[:20]:

        line = line.strip()

        if not line:
            continue

        lower_line = line.lower()

        # Skip headings
        if lower_line in HEADINGS:
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

        # All words alphabetic
        if all(word.replace('.', '').isalpha() for word in words):
            return line.title()

    return "Not Found"
# =====================================================
# EXPERIENCE EXTRACTION
# =====================================================
def extract_experience(text):

    pattern = r'(\d+)\+?\s*years?'

    matches = re.findall(pattern, text.lower())

    if matches:

        max_exp = max([int(x) for x in matches])

        return f"{max_exp} Years"

    return "Not Found"