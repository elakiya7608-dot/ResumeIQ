import streamlit as st
from resume import extract_text_from_pdf, extract_text_from_docx
from ocr_helper import extract_text_from_scanned_pdf
from keywords import get_keywords
from scorer import extract_keywords, calculate_score
from api_helper import get_ai_feedback
import pandas as pd

# =====================================================
# NEW IMPORTS FOR .ENV
# =====================================================
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path=".env")

print(os.getenv("GOOGLE_API_KEY"))


# =====================================================
# LOAD ENV VARIABLES
# =====================================================
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Optional validation
if not GOOGLE_API_KEY:
    st.error("❌ GOOGLE_API_KEY not found in .env file")
    st.stop()


# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="AI Resume Analyzer",
    layout="centered"
)

st.title("🤖 AI RESUME ANALYZER")

st.write(
    "Upload your resume(s) (PDF or DOCX) and check your AI job readiness"
)


# =====================================================
# CUSTOM EXCEPTION
# =====================================================
class EmptyResumeError(Exception):
    pass


# =====================================================
# ERROR HANDLER FUNCTIONS
# =====================================================
def show_error(message):
    st.error(message)


def show_warning(message):
    st.warning(message)


# =====================================================
# FILE UPLOAD
# =====================================================
uploaded_files = st.file_uploader(
    "Upload Resume(s)",
    type=["pdf", "docx"],
    accept_multiple_files=True
)


# =====================================================
# SUBMIT BUTTON
# =====================================================
submit = st.button("Submit")


# =====================================================
# BADGE FUNCTION
# =====================================================
def show_badges(items, color):

    badge_html = ""

    for item in items:

        badge_html += f"""
        <span style="
            background-color:{color};
            color:white;
            padding:6px 10px;
            border-radius:15px;
            margin:4px;
            display:inline-block;
            font-size:13px;
        ">
        {item}
        </span>
        """

    st.markdown(
        badge_html,
        unsafe_allow_html=True
    )

    return badge_html


# =====================================================
# MAIN LOGIC
# =====================================================
if submit:

    # =====================================================
    # CHECK FILE
    # =====================================================
    if not uploaded_files:

        st.warning(
            "⚠️ Please upload at least one resume."
        )

        st.stop()

    results = []

    # =====================================================
    # SHORTLISTED CANDIDATES
    # =====================================================
    shortlisted_candidates = []

    # =====================================================
    # PROCESS MULTIPLE RESUMES
    # =====================================================
    for uploaded_file in uploaded_files:

        # =====================================================
        # DEFAULT VALUES
        # =====================================================
        empty_resume = False
        feedback = ""
        resume_text = ""

        matched = []
        missing = []
        score = 0

        # =====================================================
        # MAIN TRY BLOCK
        # =====================================================
        try:

            # =====================================================
            # SPINNER
            # =====================================================
            with st.spinner(
                f"🔍 Analyzing {uploaded_file.name}..."
            ):

                # =====================================================
                # PDF PROCESSING
                # =====================================================
                if uploaded_file.name.endswith(".pdf"):

                    # -------------------------------------------------
                    # NORMAL PDF EXTRACTION
                    # -------------------------------------------------
                    try:

                        resume_text = extract_text_from_pdf(
                            uploaded_file
                        )

                    except Exception:
                        show_error(
                            f"❌ Failed to extract text from PDF: {uploaded_file.name}"
                        )
                        continue

                    # -------------------------------------------------
                    # OCR FALLBACK
                    # -------------------------------------------------
                    if not resume_text.strip():

                        show_warning(
                            f"⚠️ Scanned PDF detected in {uploaded_file.name}. Running OCR..."
                        )

                        try:

                            uploaded_file.seek(0)

                            resume_text = extract_text_from_scanned_pdf(
                                uploaded_file
                            )

                        except Exception:
                            show_error(
                                f"❌ OCR processing failed for {uploaded_file.name}"
                            )
                            continue

                    # -------------------------------------------------
                    # EMPTY PDF
                    # -------------------------------------------------
                    if len(resume_text.strip()) == 0:

                        raise EmptyResumeError(
                            "Resume content is empty"
                        )

                # =====================================================
                # DOCX PROCESSING
                # =====================================================
                elif uploaded_file.name.endswith(".docx"):

                    try:

                        resume_text = extract_text_from_docx(
                            uploaded_file
                        )

                    except Exception:
                        show_error(
                            f"❌ Failed to extract text from DOCX: {uploaded_file.name}"
                        )
                        continue

                    # -------------------------------------------------
                    # EMPTY DOCX
                    # -------------------------------------------------
                    if len(resume_text.strip()) == 0:

                        raise EmptyResumeError(
                            "Resume content is empty"
                        )

                # =====================================================
                # INVALID FILE FORMAT
                # =====================================================
                else:

                    show_error(
                        f"❌ Unsupported file format: {uploaded_file.name}"
                    )

                    continue

                # =====================================================
                # KEYWORD EXTRACTION
                # =====================================================
                try:

                    keywords = get_keywords()

                    matched, missing = extract_keywords(
                        resume_text,
                        keywords
                    )

                except Exception:
                    show_error(
                        f"❌ Keyword extraction failed for {uploaded_file.name}"
                    )
                    continue

                # =====================================================
                # SCORE CALCULATION
                # =====================================================
                try:

                    score = calculate_score(
                        matched,
                        keywords
                    )

                except Exception:
                    show_error(
                        f"❌ Score calculation failed for {uploaded_file.name}"
                    )
                    continue

                # =====================================================
                # AI FEEDBACK
                # =====================================================
                try:

                    feedback = get_ai_feedback(
                        resume_text,
                        matched,
                        score
                    )

                except Exception:

                    feedback = (
                        "⚠️ AI feedback service is currently unavailable."
                    )

                    show_warning(
                        f"AI feedback generation failed for {uploaded_file.name}"
                    )

        # =====================================================
        # EMPTY RESUME ERROR
        # =====================================================
        except EmptyResumeError as e:

            empty_resume = True

            feedback = (
                "The uploaded resume appears to be empty. "
                "Please upload a valid resume."
            )

            show_warning(
                f"⚠️ {uploaded_file.name}: {str(e)}"
            )

        # =====================================================
        # UNEXPECTED ERROR
        # =====================================================
        except Exception:

            show_error(
                f"❌ Unexpected error occurred while processing {uploaded_file.name}"
            )

            continue

        # =====================================================
        # FINALLY BLOCK
        # =====================================================
        finally:

            # Reset file pointer safely
            try:
                uploaded_file.seek(0)

            except Exception:
                pass

        # =====================================================
        # DISPLAY RESULTS FOR EACH RESUME
        # =====================================================
        st.divider()

        st.subheader(
            f"📄 Resume: {uploaded_file.name}"
        )

        # =====================================================
        # SCORE
        # =====================================================
        st.markdown(
            f"""
            <h3 style='color:green;'>
            📊 Resume Score: {score}%
            </h3>
            """,
            unsafe_allow_html=True
        )

        # =====================================================
        # PROGRESS BAR
        # =====================================================
        st.progress(int(score))

        # =====================================================
        # KEYWORDS SECTION
        # =====================================================
        col1, col2 = st.columns(2)

        # =====================================================
        # MATCHED KEYWORDS
        # =====================================================
        with col1:

            st.subheader("✅ Matched Keywords")

            if matched:

                show_badges(
                    matched,
                    "#57BD5B"
                )

            else:

                st.write(
                    "No matched keywords"
                )

        # =====================================================
        # MISSING KEYWORDS
        # =====================================================
        with col2:

            st.subheader("❌ Missing Keywords")

            if missing:

                show_badges(
                    missing,
                    "#ec392c"
                )

            else:

                st.write(
                    "No missing keywords 🎉"
                )

        # =====================================================
        # AI FEEDBACK
        # =====================================================
        st.subheader("💡 AI Feedback")

        st.text_area(
            f"AI Suggestion - {uploaded_file.name}",
            value=feedback,
            height=200
        )

        # =====================================================
        # SHORTLISTED CANDIDATES
        # =====================================================
        if score >= 80 and not empty_resume:

            shortlisted_candidates.append({

                "Resume Name": uploaded_file.name,

                "Score": score

            })

        # =====================================================
        # STORE RESULTS
        # =====================================================
        results.append({

            "Resume Name": uploaded_file.name,

            "Score": score
            if not empty_resume
            else 0,

            "Matched Keywords": len(matched)
            if not empty_resume
            else 0,

            "Missing Keywords": len(missing)
            if not empty_resume
            else 0,

            "Feedback": feedback
        })

    # =====================================================
    # FINAL OUTPUT
    # =====================================================
    st.success(
        "✅ Resume analysis completed successfully!"
    )

    # =====================================================
    # DATAFRAME
    # =====================================================
    df = pd.DataFrame(results)

    # =====================================================
    # SORT BY SCORE
    # =====================================================
    df = df.sort_values(
        by="Score",
        ascending=False
    )

    # =====================================================
    # COMPARISON TABLE
    # =====================================================
    if len(uploaded_files) > 1:

        st.subheader(
            "📊 Resume Comparison Table"
        )

        st.dataframe(
            df,
            use_container_width=True
        )

    # =====================================================
    # SHORTLISTED CANDIDATES TABLE
    # =====================================================
    st.divider()

    st.subheader("🏆 Shortlisted Candidates")

    if shortlisted_candidates:

        shortlisted_df = pd.DataFrame(
            shortlisted_candidates
        )

        shortlisted_df = shortlisted_df.sort_values(
            by="Score",
            ascending=False
        )

        st.dataframe(
            shortlisted_df,
            use_container_width=True
        )

    else:

        st.warning(
            "❌ No candidates shortlisted"
        )