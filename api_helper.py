import warnings
warnings.filterwarnings("ignore")

import google.generativeai as genai
import os
from dotenv import load_dotenv

# LOAD ENV FILE
load_dotenv()

# GET API KEY FROM .ENV
api_key = os.getenv("GOOGLE_API_KEY")

print("Loaded API Key:", api_key)

# CONFIGURE GEMINI
genai.configure(api_key=api_key)
# ---------------- LOAD MODEL ----------------
model = genai.GenerativeModel("gemini-2.5-flash-lite")


# =====================================================
# AI FEEDBACK FUNCTION
# =====================================================
def get_ai_feedback(resume_text, matched_keywords, score):

    try:

        # =================================================
        # EMPTY RESUME
        # =================================================
        if resume_text == "Empty Resume":

            prompt = """
A user uploaded an empty or unreadable resume.

Explain professionally:
- the resume is empty
- possible reasons
- how to fix it
- what type of resume should be uploaded

Keep the response short and professional.
"""

        # =================================================
        # NORMAL RESUME
        # =================================================
        else:

            # Convert keyword list to string
            keywords_str = ", ".join(
                [str(k) for k in matched_keywords]
            )

            prompt = f"""
You are an HR expert.

Candidate Resume:
{resume_text}

Matched Skills:
{keywords_str}

Resume Score: {score}%

Give:
1. 3-line professional feedback
2. Candidate suitability for AI role
3. Suggestions to improve

Keep it short and clear.
"""

        print("Calling Gemini API...")

        # Generate response
        response = model.generate_content(prompt)

        # Safety check
        if response and hasattr(response, "text"):

            return response.text.strip()

        else:

            return "No AI feedback generated."

    # =================================================
    # ERROR HANDLING
    # =================================================
    except Exception as e:

        return f"Error: {str(e)}"


# =====================================================
# TESTING SECTION
# =====================================================
from resume import extract_text_from_pdf

if __name__ == "__main__":

    resume_text = extract_text_from_pdf("resume1.pdf")

    keywords = ["Python", "AI", "ML"]

    score = 50

    feedback = get_ai_feedback(
        resume_text,
        keywords,
        score
    )

    print(feedback)