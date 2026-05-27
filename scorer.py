import re


# =====================================================
# KEYWORD EXTRACTION
# =====================================================
def extract_keywords(resume_text, keyword_list):

    matched = []
    missing = []

    # Convert resume text to lowercase
    resume_text_lower = resume_text.lower()

    # Loop through keywords
    for word in keyword_list:

        # =================================================
        # SINGLE WORD MATCH (WORD BOUNDARY)
        # =================================================
        if len(word.split()) == 1:

            pattern = r'\b' + re.escape(word.lower()) + r'\b'

            if re.search(pattern, resume_text_lower):

                matched.append(word)

            else:

                missing.append(word)

        # =================================================
        # MULTI-WORD MATCH
        # =================================================
        else:

            if word.lower() in resume_text_lower:

                matched.append(word)

            else:

                missing.append(word)

    return matched, missing


# =====================================================
# SCORE CALCULATION
# =====================================================
def calculate_score(matched, total):

    # Prevent division by zero
    if len(total) == 0:

        return 0

    score = (len(matched) / len(total)) * 100

    return round(score, 2)