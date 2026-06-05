import warnings
warnings.filterwarnings("ignore")

import google.generativeai as genai
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

# =====================================================
# EXACT JSON SCHEMAS — injected verbatim into prompts
# =====================================================
SCHEMA_INVALID = '''{
    "status": "invalid",
    "message": "<your message here>"
}'''

SCHEMA_VALID = '''{
    "professional_feedback": "<your feedback here>",
    "candidate_suitability": "<your suitability analysis here>",
    "resume_score": 0,
    "matched_skills": [],
    "suggestions": []
}'''

# =====================================================
# SYSTEM INSTRUCTION
# =====================================================
SYSTEM_INSTRUCTION = """
You are a professional ATS Resume Analyzer.

STRICT OUTPUT RULES — follow every rule exactly:

RULE 1: Your ENTIRE response must be ONE valid JSON object. Nothing else.
RULE 2: Do NOT write any text before or after the JSON.
RULE 3: Do NOT use markdown. Do NOT use ```json or ``` anywhere.
RULE 4: Do NOT add extra keys beyond what the schema specifies.
RULE 5: Do NOT leave placeholder text like "<your message here>" — replace it with real content.
RULE 6: All string values must be complete sentences. No empty strings.
RULE 7: The "suggestions" array must contain strings, not objects.
RULE 8: "resume_score" must be an integer (the exact score passed to you), not a string.

Violating any rule makes your response useless. Return ONLY the JSON object.
"""

# =====================================================
# MODEL — temperature=0 for deterministic JSON output
# =====================================================
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash-lite",
    system_instruction=SYSTEM_INSTRUCTION,
    generation_config=genai.GenerationConfig(
        temperature=0.0,
        top_p=1,
        top_k=1,
    )
)


# =====================================================
# JSON EXTRACTOR — strips accidental markdown fences
# even with temperature=0, defensive parsing is wise
# =====================================================
def _extract_json(raw: str) -> dict:
    """
    Attempts to parse JSON from the raw AI response.
    Handles edge cases:
      - Wrapped in ```json ... ```
      - Leading/trailing whitespace or newlines
      - Stray text before/after the JSON object
    """
    # Strip markdown fences
    cleaned = re.sub(r"```(?:json)?", "", raw).strip()

    # Try direct parse first
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Try extracting first {...} block (handles stray prefix/suffix text)
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Give up — return a safe fallback dict
    return {
        "status": "error",
        "message": "The AI returned a response that could not be parsed. Please try again.",
        "raw_response": raw[:500]
    }


# =====================================================
# PROMPT BUILDERS — one per case, schema injected
# =====================================================

def _prompt_empty() -> str:
    return f"""
A user uploaded a resume file but NO TEXT could be extracted from it.
The file is blank, corrupted, or completely unreadable.

Your task: Return a polite, helpful explanation as JSON.

You MUST return ONLY this JSON structure, with the message field filled in:
{SCHEMA_INVALID}

Fill "message" with: A warm 1-2 sentence explanation that the file appears empty
and asks the user to upload a valid PDF or DOCX resume with actual text content.

Return ONLY the JSON. No other text.
"""


def _prompt_too_short(text: str, word_count: int) -> str:
    return f"""
A user uploaded a file for resume analysis.
The ENTIRE extracted text from the file is shown below — only {word_count} word(s).
This is far too short to be a resume.

Extracted text:
---
{text}
---

Your task: Return a polite explanation as JSON.

You MUST return ONLY this JSON structure, with the message field filled in:
{SCHEMA_INVALID}

Fill "message" with: A warm 1-2 sentence explanation that the content is too short
to be a resume, mention what was found if helpful, and ask them to upload their
actual resume document.

Return ONLY the JSON. No other text.
"""


def _prompt_not_a_resume(text: str) -> str:
    return f"""
A user uploaded a document for resume analysis, but it does NOT appear to be a resume or CV.
It may be a company policy, invoice, article, report, or other non-resume document.

Beginning of the extracted text:
---
{text[:600]}
---

Your task: Return a polite explanation as JSON.

You MUST return ONLY this JSON structure, with the message field filled in:
{SCHEMA_INVALID}

Fill "message" with: A polite 1-2 sentence explanation that this document does not
look like a resume, briefly describe what it seems to be (based on the text above),
and ask the user to upload their actual resume or CV.

Return ONLY the JSON. No other text.
"""


def _prompt_valid_resume(resume_text: str, matched_keywords: list, score: int) -> str:
    keywords_str = ", ".join(str(k) for k in matched_keywords) if matched_keywords else "None"

    return f"""
Analyze the following resume professionally for ATS suitability.

--- RESUME TEXT START ---
{resume_text}
--- RESUME TEXT END ---

Matched Skills: {keywords_str}
ATS Score: {score}%

You MUST return ONLY this JSON structure with all fields filled in:
{SCHEMA_VALID}

Field instructions:
- "professional_feedback": 2-3 sentences on overall resume quality and ATS readiness.
- "candidate_suitability": 1-2 sentences on how well the candidate fits AI/software roles.
- "resume_score": use exactly {score} (integer, not string).
- "matched_skills": list of matched skill strings from the resume (use the matched skills above).
- "suggestions": list of 3-5 specific improvement suggestions as plain strings.

Return ONLY the JSON. No other text.
"""


# =====================================================
# MAIN FUNCTION
# =====================================================
def get_ai_feedback(resume_text: str, matched_keywords: list, score: int) -> dict:

    text = (resume_text or "").strip()
    word_count = len(text.split())

    # ── Detect which case applies ──────────────────────────────────────────
    if not text:
        prompt = _prompt_empty()

    elif word_count < 30:
        prompt = _prompt_too_short(text, word_count)

    else:
        # Heuristic: check for resume signal words
        resume_signals = {
            "experience", "education", "skills", "work", "employment",
            "qualification", "certification", "project", "objective",
            "summary", "achievement", "responsibility", "university",
            "degree", "internship", "volunteer", "profile", "career"
        }
        text_lower = text.lower()
        has_resume_signal = any(sig in text_lower for sig in resume_signals)

        if not has_resume_signal and score < 10:
            prompt = _prompt_not_a_resume(text)
        else:
            prompt = _prompt_valid_resume(resume_text, matched_keywords, score)

    # ── Call Gemini ────────────────────────────────────────────────────────
    try:
        print("Calling Gemini API...")
        response = model.generate_content(prompt)

        if not (response and hasattr(response, "text") and response.text):
            return {
                "status": "error",
                "message": "The AI did not return a response. Please try again."
            }

        raw = response.text
        print("\nRAW AI RESPONSE:\n", raw)

        result = _extract_json(raw)

        # ── Post-parse validation: ensure resume_score is int ─────────────
        if "resume_score" in result:
            try:
                result["resume_score"] = int(result["resume_score"])
            except (ValueError, TypeError):
                result["resume_score"] = score

        return result

    except Exception as e:
        return {
            "status": "error",
            "message": f"An error occurred while contacting the AI service: {str(e)}"
        }