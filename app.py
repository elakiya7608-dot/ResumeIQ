import streamlit as st
from resume import extract_text_from_pdf, extract_text_from_docx
from ocr_helper import (
    extract_text_from_scanned_pdf,
    extract_text_from_docx_images
)
from candidate_parser import (
    extract_name,
    extract_email,
    extract_phone,
    extract_experience
)
from keywords import get_keywords
from scorer import extract_keywords, calculate_score
from api_helper import get_ai_feedback
from validator import validate_resume
import pandas as pd
import os
import tempfile
from dotenv import load_dotenv

# =====================================================
# LOAD ENVIRONMENT VARIABLES
# =====================================================
load_dotenv(dotenv_path=".env")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    st.error("❌ GOOGLE_API_KEY not found in .env file")
    st.stop()

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="ResumeIQ – AI Resume Analyzer",
    page_icon="🤖",
    layout="wide"
)

# =====================================================
# GLOBAL STYLES
# =====================================================
st.markdown("""
    <style>
        /* ---- Base ---- */
        html, body, [class*="css"] {
            font-family: 'Segoe UI', sans-serif;
        }

        /* ---- Header ---- */
        .main-header {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            padding: 2rem 2.5rem;
            border-radius: 16px;
            margin-bottom: 1.5rem;
            color: white;
        }
        .main-header h1 {
            font-size: 2.4rem;
            font-weight: 800;
            margin: 0;
            letter-spacing: -0.5px;
            color: #ffffff !important;
        }
        .main-header p {
            color: #94a3b8;
            margin: 0.4rem 0 0 0;
            font-size: 1rem;
        }

        /* ---- Score Card ---- */
        .score-card {
            background: linear-gradient(135deg, #0f3460, #533483);
            color: white;
            padding: 1.5rem 2rem;
            border-radius: 14px;
            text-align: center;
            margin: 1rem 0;
        }
        .score-card .score-number {
            font-size: 3rem;
            font-weight: 900;
            line-height: 1;
        }
        .score-card .score-label {
            font-size: 0.9rem;
            color: #cbd5e1;
            margin-top: 0.25rem;
        }

        /* ---- Info Card ---- */
        .info-card {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 1.2rem 1.5rem;
            margin-bottom: 1rem;
        }
        .info-card .label {
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #64748b;
            margin-bottom: 0.2rem;
        }
        .info-card .value {
            font-size: 1rem;
            font-weight: 600;
            color: #1e293b;
        }

        /* ---- Badge ---- */
        .badge-green {
            display: inline-block;
            background: #dcfce7;
            color: #166534;
            border: 1px solid #bbf7d0;
            padding: 5px 12px;
            border-radius: 999px;
            font-size: 0.82rem;
            font-weight: 600;
            margin: 3px 4px 3px 0;
        }
        .badge-red {
            display: inline-block;
            background: #fee2e2;
            color: #991b1b;
            border: 1px solid #fecaca;
            padding: 5px 12px;
            border-radius: 999px;
            font-size: 0.82rem;
            font-weight: 600;
            margin: 3px 4px 3px 0;
        }

        /* ---- Validation Error Banner ---- */
        .validation-error {
            background: #fff1f2;
            border: 2px solid #fda4af;
            border-radius: 12px;
            padding: 1.2rem 1.5rem;
            margin: 1rem 0;
            color: #881337;
        }
        .validation-error .v-title {
            font-size: 1rem;
            font-weight: 700;
            margin-bottom: 0.4rem;
        }
        .validation-error .v-msg {
            font-size: 0.92rem;
            line-height: 1.6;
        }

        /* ---- Section Header ---- */
        .section-title {
            font-size: 1rem;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 0.75rem;
            padding-bottom: 0.4rem;
            border-bottom: 2px solid #e2e8f0;
        }

        /* ---- Shortlisted ---- */
        .shortlisted-badge {
            background: linear-gradient(90deg, #22c55e, #16a34a);
            color: white;
            padding: 4px 14px;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 700;
            display: inline-block;
            margin-left: 0.5rem;
        }

        /* ---- Divider ---- */
        .styled-divider {
            border: none;
            border-top: 1px solid #e2e8f0;
            margin: 1.5rem 0;
        }

        /* ---- Sidebar ---- */
        [data-testid="stSidebar"] {
            background: #0f172a;
        }
        [data-testid="stSidebar"] * {
            color: #e2e8f0 !important;
        }
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            color: #f8fafc !important;
        }

        /* ---- Sidebar Keyword Badges ---- */
        .badge-sidebar-kw {
            display: inline-block;
            background: #1e3a5f;
            color: #7dd3fc !important;
            border: 1px solid #38bdf8;
            padding: 4px 11px;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 600;
            margin: 3px 4px 3px 0;
        }

        /* ---- Tab Styling ---- */
        .stTabs [data-baseweb="tab-list"] {
            gap: 6px;
            background: #f1f5f9;
            padding: 4px;
            border-radius: 10px;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px;
            padding: 8px 20px;
            font-weight: 600;
            font-size: 0.9rem;
            color: #64748b;
        }
        .stTabs [aria-selected="true"] {
            background: white;
            color: #0f3460 !important;
            box-shadow: 0 1px 4px rgba(0,0,0,0.12);
        }

        /* ---- Feedback Boxes ---- */
        .feedback-box {
            background: #f0f9ff;
            border-left: 4px solid #0ea5e9;
            border-radius: 0 10px 10px 0;
            padding: 1rem 1.25rem;
            color: #0c4a6e;
            font-size: 0.95rem;
            line-height: 1.6;
            margin-bottom: 1rem;
        }
        .suitability-box {
            background: #f0fdf4;
            border-left: 4px solid #22c55e;
            border-radius: 0 10px 10px 0;
            padding: 1rem 1.25rem;
            color: #14532d;
            font-size: 0.95rem;
            line-height: 1.6;
            margin-bottom: 1rem;
        }
        .suggestion-item {
            background: #fefce8;
            border-left: 4px solid #eab308;
            border-radius: 0 8px 8px 0;
            padding: 0.6rem 1rem;
            margin-bottom: 0.5rem;
            color: #713f12;
            font-size: 0.9rem;
        }

        /* ---- Score Color ---- */
        .score-high  { color: #16a34a; font-weight: 800; font-size: 2.5rem; }
        .score-mid   { color: #d97706; font-weight: 800; font-size: 2.5rem; }
        .score-low   { color: #dc2626; font-weight: 800; font-size: 2.5rem; }

        /* ---- Upload Section ---- */
        .upload-section {
            background: #f8fafc;
            border: 2px dashed #cbd5e1;
            border-radius: 14px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }

        /* ---- Metric Card ---- */
        .metric-card {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 1rem 1.25rem;
            text-align: center;
        }
        .metric-card .metric-num {
            font-size: 2rem;
            font-weight: 800;
            color: #0f3460;
        }
        .metric-card .metric-lbl {
            font-size: 0.78rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #94a3b8;
            margin-top: 0.2rem;
        }
    </style>
""", unsafe_allow_html=True)


# =====================================================
# CUSTOM EXCEPTIONS
# =====================================================
class EmptyResumeError(Exception):
    pass


# =====================================================
# HELPER FUNCTIONS
# =====================================================
def show_error(message):
    st.error(message)


def show_warning(message):
    st.warning(message)


def render_badges(items, badge_class):
    html = "".join(
        f'<span class="{badge_class}">{item}</span>'
        for item in items
    )
    st.markdown(html, unsafe_allow_html=True)


def score_color_class(score):
    if score >= 80:
        return "score-high"
    elif score >= 50:
        return "score-mid"
    return "score-low"


def score_label(score):
    if score >= 80:
        return "🌟 Excellent Match"
    elif score >= 60:
        return "👍 Good Match"
    elif score >= 40:
        return "⚠️ Fair Match"
    return "❌ Low Match"


# =====================================================
# SIDEBAR 
# =====================================================
with st.sidebar:
    st.markdown("## 🤖 ResumeIQ")
    st.markdown("**AI-Powered Resume Analysis**")
    st.markdown("---")

    with st.expander("ℹ️ About ResumeIQ", expanded=True):
        st.markdown("""
        **ResumeIQ** analyzes resumes against industry
        keywords, scores candidates, and provides
        AI-driven feedback.

        - 📄 PDF & DOCX Support 
        - 🔍 OCR for scanned documents
        - 🤖 Google Gemini AI feedback
        - 📊 Multi-resume comparison
        - 🏆 Auto shortlisting (score ≥ 80%)
        """)

    st.markdown("### 📋 Keyword Reference")
    try:
        all_keywords = get_keywords()
        with st.expander(f"View All Keywords ({len(all_keywords)})", expanded=False):
            html = "".join(
                f'<span class="badge-sidebar-kw">{kw}</span>'
                for kw in sorted(all_keywords)
            )
            st.markdown(html, unsafe_allow_html=True)
    except Exception:
        st.warning("Keywords unavailable")

    st.markdown("---")

    with st.expander("📊 Scoring Guide", expanded=False):
        st.markdown("""
        | Score | Rating |
        |-------|--------|
        | 80–100% | 🌟 Excellent |
        | 60–79%  | 👍 Good |
        | 40–59%  | ⚠️ Fair |
        | 0–39%   | ❌ Low |

        Candidates with **score ≥ 80%** are automatically
        added to the Shortlisted Candidates table.
        """)

    with st.expander("💡 Tips for Better Score", expanded=False):
        st.markdown("""
        - Include relevant technical skills explicitly
        - Use industry-standard terminology
        - List tools, frameworks, and technologies
        - Include certifications and coursework
        - Quantify achievements where possible
        """)

    st.markdown("---")
    st.caption("Built with Streamlit + Google Gemini")


# =====================================================
# MAIN HEADER
# =====================================================
st.markdown("""
    <div class="main-header">
        <h1>🤖 ResumeIQ</h1>
        <p>Upload your resume(s) and get an instant AI-powered job readiness analysis</p>
    </div>
""", unsafe_allow_html=True)


# =====================================================
# FILE UPLOAD SECTION
# =====================================================
st.markdown('<div class="upload-section">', unsafe_allow_html=True)
uploaded_files = st.file_uploader(
    "📂 Upload Resume(s) — PDF or DOCX",
    type=["pdf", "docx"],
    accept_multiple_files=True,
    help="You can upload multiple resumes for comparison"
)

col_a, col_b, col_c = st.columns([1, 1, 2])
with col_a:
    submit = st.button("🚀 Analyze Resume(s)", use_container_width=True, type="primary")
with col_b:
    if uploaded_files:
        st.markdown(
            f'<div style="padding:0.5rem 0; color:#475569; font-size:0.9rem;">'
            f'📎 {len(uploaded_files)} file(s) selected</div>',
            unsafe_allow_html=True
        )
st.markdown('</div>', unsafe_allow_html=True)


# =====================================================
# MAIN LOGIC
# =====================================================
if submit:

    # ── Guard: no files uploaded ──────────────────────
    if not uploaded_files:
        st.warning("⚠️ Please upload at least one resume before clicking Analyze.")
        st.stop()

    results = []
    shortlisted_candidates = []
    any_valid_resume_processed = False

    for uploaded_file in uploaded_files:

        # Default values
        empty_resume = False
        feedback = ""
        resume_text = ""
        matched = []
        missing = []
        score = 0
        candidate_name = "Not Found"
        candidate_email = "Not Found"
        candidate_phone = "Not Found"
        candidate_experience = "Not Found"

        # ── Read file bytes ONCE ──
        file_bytes = uploaded_file.read()

        # =====================================================
        # STEP 1 — RESUME VALIDATION
        # =====================================================
        with st.spinner(f"🛡️ Validating {uploaded_file.name}..."):
            is_valid_resume, validation_msg, validation_details = validate_resume(
                file_bytes, uploaded_file.name
            )

        if not is_valid_resume:
            reason = validation_details.get("reason")

            # ── HARD REJECT: too long or official/legal doc ──────────────
            if reason in ("too_long", "hard_block"):
                st.markdown("<hr class='styled-divider'>", unsafe_allow_html=True)
                st.markdown(
                    f"""
                    <div class="validation-error">
                        <div class="v-title">📄 {uploaded_file.name} — Rejected</div>
                        <div class="v-msg">{validation_msg}<br><br>
                        <strong>Please upload a valid resume or CV (PDF / DOCX).</strong></div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                continue

            # ── SOFT REJECT: empty file or low keyword count ─────────────
            if reason in ("empty", "not_resume"):
                empty_resume = True
                any_valid_resume_processed = True
                try:
                    feedback = get_ai_feedback("", [], 0)
                except Exception:
                    feedback = {
                        "status": "invalid",
                        "message": (
                            "The uploaded file appears to be empty or does not look "
                            "like a resume. Please upload a valid PDF or DOCX resume "
                            "with actual text content."
                        )
                    }
                score  = 0
                matched = []
                missing = []
                is_shortlisted = False

                st.markdown("<hr class='styled-divider'>", unsafe_allow_html=True)
                st.markdown(
                    f'<h2 style="color:#1e293b; margin-bottom:0.25rem;">📄 {uploaded_file.name}</h2>',
                    unsafe_allow_html=True
                )

                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    st.markdown(
                        '<div class="metric-card"><div class="score-low">0%</div>'
                        '<div class="metric-lbl">Match Score</div></div>',
                        unsafe_allow_html=True
                    )
                with m2:
                    st.markdown(
                        '<div class="metric-card"><div class="metric-num" style="color:#16a34a">0</div>'
                        '<div class="metric-lbl">Matched Keywords</div></div>',
                        unsafe_allow_html=True
                    )
                with m3:
                    st.markdown(
                        '<div class="metric-card"><div class="metric-num" style="color:#dc2626">0</div>'
                        '<div class="metric-lbl">Missing Keywords</div></div>',
                        unsafe_allow_html=True
                    )
                with m4:
                    st.markdown(
                        '<div class="metric-card"><div style="font-size:1.4rem; margin-top:0.2rem">❌</div>'
                        '<div class="metric-lbl">Low Match</div></div>',
                        unsafe_allow_html=True
                    )

                st.markdown("<br>", unsafe_allow_html=True)

                tab1, tab2, tab3 = st.tabs([
                    "📊 Results",
                    "👤 Candidate Info",
                    "💡 AI Feedback"
                ])

                with tab1:
                    st.info("No keyword data available — file could not be read as a resume.")

                with tab2:
                    st.info("No candidate information available.")

                with tab3:
                    feedback_status = feedback.get("status") if isinstance(feedback, dict) else None
                    icon = "🤖" if feedback_status == "invalid" else "⚠️"
                    message = (
                        feedback.get("message", "Unable to process this file.")
                        if isinstance(feedback, dict)
                        else str(feedback)
                    )
                    st.markdown(
                        f'<div class="feedback-box">{icon} {message}</div>',
                        unsafe_allow_html=True
                    )

                results.append({
                    "Resume Name":      uploaded_file.name,
                    "Candidate Name":   "Not Found",
                    "Score":            0,
                    "Matched Keywords": 0,
                    "Missing Keywords": 0,
                    "Status":           "Not Shortlisted",
                })

                continue

        any_valid_resume_processed = True

        # Write bytes to temp file
        suffix = os.path.splitext(uploaded_file.name)[1]
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                tmp_file.write(file_bytes)
                temp_path = tmp_file.name
        except Exception:
            show_error(f"❌ Could not create temporary file for {uploaded_file.name}")
            continue

        # =====================================================
        # STEP 2 - MAIN ANALYSIS
        # =====================================================
        try:
            with st.spinner(f"🔍 Analyzing {uploaded_file.name}..."):

                # --- PDF ---
                if uploaded_file.name.lower().endswith(".pdf"):
                    try:
                        import io as _io
                        resume_text = extract_text_from_pdf(_io.BytesIO(file_bytes))
                        
                    except Exception:
                        show_error(f"❌ Failed to extract text from PDF: {uploaded_file.name}")
                        continue

                    if not resume_text.strip():
                        show_warning(f"⚠️ Scanned PDF detected in {uploaded_file.name}. Running OCR...")
                        try:
                            resume_text = extract_text_from_scanned_pdf(temp_path)
                        except Exception:
                            show_error(f"❌ OCR processing failed for {uploaded_file.name}")
                            continue

                    if len(resume_text.strip()) == 0:
                        raise EmptyResumeError("Resume content is empty after extraction")

                # --- DOCX ---
                elif uploaded_file.name.lower().endswith(".docx"):
                    try:
                        import io as _io
                        resume_text = extract_text_from_docx(_io.BytesIO(file_bytes))
                    except Exception:
                        show_error(f"❌ Failed to extract text from DOCX: {uploaded_file.name}")
                        continue

                    if not resume_text.strip():
                        show_warning(f"⚠️ Image-based DOCX detected in {uploaded_file.name}. Running OCR...")
                        try:
                            resume_text = extract_text_from_docx_images(temp_path)
                        except Exception:
                            show_error(f"❌ OCR processing failed for {uploaded_file.name}")
                            continue

                    if len(resume_text.strip()) == 0:
                        raise EmptyResumeError("Resume content is empty after extraction")

                # --- Keyword Extraction ---
                try:
                    keywords = get_keywords()
                    matched, missing = extract_keywords(resume_text, keywords)
                    
                except Exception:
                    show_error(f"❌ Keyword extraction failed for {uploaded_file.name}")
                    continue

                # --- Score ---
                try:
                    score = calculate_score(matched, keywords)
                    
                except Exception:
                    show_error(f"❌ Score calculation failed for {uploaded_file.name}")
                    continue

                # --- AI Feedback ---
                try:
                    
                    feedback = get_ai_feedback(resume_text, matched, score)
                    
                except Exception:
                    feedback = "⚠️ AI feedback service is currently unavailable."
                    show_warning(f"AI feedback generation failed for {uploaded_file.name}")

                # --- Candidate Info ---
                candidate_name       = extract_name(resume_text)
                candidate_email      = extract_email(resume_text)
                candidate_phone      = extract_phone(resume_text)
                candidate_experience = extract_experience(resume_text)

        except EmptyResumeError as e:
            empty_resume = True
            feedback = "The uploaded resume appears to be empty. Please upload a valid resume."
            show_warning(f"⚠️ {uploaded_file.name}: {str(e)}")

        except Exception:
            show_error(f"❌ Unexpected error occurred while processing {uploaded_file.name}")
            continue

        finally:
            try:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass

        # =====================================================
        # DISPLAY RESULTS
        # =====================================================
        st.markdown("<hr class='styled-divider'>", unsafe_allow_html=True)

        # Resume file header + shortlist badge
        is_shortlisted = score >= 80 and not empty_resume
        shortlist_badge = '<span class="shortlisted-badge">🏆 Shortlisted</span>' if is_shortlisted else ""
        st.markdown(
            f'<h2 style="color:#1e293b; margin-bottom:0.25rem;">📄 {uploaded_file.name} {shortlist_badge}</h2>',
            unsafe_allow_html=True
        )

        # Quick metrics row
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            cls = score_color_class(score)
            st.markdown(
                f'<div class="metric-card"><div class="{cls}">{score}%</div>'
                f'<div class="metric-lbl">Match Score</div></div>',
                unsafe_allow_html=True
            )
        with m2:
            st.markdown(
                f'<div class="metric-card"><div class="metric-num" style="color:#16a34a">{len(matched)}</div>'
                f'<div class="metric-lbl">Matched Keywords</div></div>',
                unsafe_allow_html=True
            )
        with m3:
            st.markdown(
                f'<div class="metric-card"><div class="metric-num" style="color:#dc2626">{len(missing)}</div>'
                f'<div class="metric-lbl">Missing Keywords</div></div>',
                unsafe_allow_html=True
            )
        with m4:
            lbl = score_label(score)
            st.markdown(
                f'<div class="metric-card"><div style="font-size:1.4rem; margin-top:0.2rem">{lbl.split()[0]}</div>'
                f'<div class="metric-lbl">{" ".join(lbl.split()[1:])}</div></div>',
                unsafe_allow_html=True
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Progress bar
        progress_color = "#16a34a" if score >= 80 else "#d97706" if score >= 50 else "#dc2626"
        st.markdown(f"""
            <div style="background:#e2e8f0; border-radius:999px; height:10px; margin-bottom:1.5rem;">
                <div style="background:{progress_color}; width:{score}%; height:10px;
                            border-radius:999px; transition:width 0.6s ease;"></div>
            </div>
        """, unsafe_allow_html=True)

        # =====================================================
        # TABS
        # =====================================================
        tab1, tab2, tab3 = st.tabs([
            "📊 Results",
            "👤 Candidate Info",
            "💡 AI Feedback"
        ])

        # --------------------------------------------------
        # TAB 1 - RESULTS
        # --------------------------------------------------
        with tab1:
            st.markdown('<p class="section-title">Keyword Analysis</p>', unsafe_allow_html=True)

            col_matched, col_missing = st.columns(2)

            with col_matched:
                st.markdown(
                    f'<p style="font-weight:700; color:#166534; margin-bottom:0.5rem;">'
                    f'✅ Matched Keywords ({len(matched)})</p>',
                    unsafe_allow_html=True
                )
                if matched:
                    render_badges(matched, "badge-green")
                else:
                    st.info("No matched keywords found.")

            with col_missing:
                st.markdown(
                    f'<p style="font-weight:700; color:#991b1b; margin-bottom:0.5rem;">'
                    f'❌ Missing Keywords ({len(missing)})</p>',
                    unsafe_allow_html=True
                )
                if missing:
                    render_badges(missing, "badge-red")
                else:
                    st.success("🎉 No missing keywords!")

            # =====================================================
            # PIE CHART - MATCHED VS MISSING SKILLS
            # =====================================================
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<p class="section-title">📊 Keyword Match Distribution</p>', unsafe_allow_html=True)

            if matched or missing:
                import plotly.graph_objects as go

                pie_labels = ["Matched ", "Missing "]
                pie_values = [len(matched), len(missing)]
                pie_colors = ["#22c55e", "#ef4444"]

                # Build hover text listing each keyword
                matched_hover = "<br>".join(matched) if matched else "None"
                missing_hover = "<br>".join(missing) if missing else "None"
                pie_hover = [
                    f"<b>Matched ({len(matched)})</b><br>{matched_hover}",
                    f"<b>Missing ({len(missing)})</b><br>{missing_hover}",
                ]

                fig_pie = go.Figure(
                    go.Pie(
                        labels=pie_labels,
                        values=pie_values,
                        marker=dict(
                            colors=pie_colors,
                            line=dict(color="#ffffff", width=2),
                        ),
                        hole=0.45,
                        hovertemplate="%{customdata}<extra></extra>",
                        customdata=pie_hover,
                        textinfo="label+percent",
                        textfont=dict(size=13, family="Segoe UI"),
                        pull=[0.04, 0.04],
                    )
                )

                fig_pie.update_layout(
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    height=380,
                    margin=dict(t=40, b=40, l=20, r=20),
                    font=dict(family="Segoe UI", size=13),
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.15,
                        xanchor="center",
                        x=0.5,
                        font=dict(size=13),
                    ),
                    annotations=[
                        dict(
                            text=(
                                f"<b>{score}%</b><br>Match"
                            ),
                            x=0.5, y=0.5,
                            font=dict(size=16, family="Segoe UI", color="#1e293b"),
                            showarrow=False,
                        )
                    ],
                )

                # Center the pie chart nicely
                pie_col1, pie_col2, pie_col3 = st.columns([1, 2, 1])
                with pie_col2:
                    st.plotly_chart(fig_pie, use_container_width=True)

                # Summary note below the chart
                total_kw = len(matched) + len(missing)
                if total_kw > 0:
                    match_pct = round((len(matched) / total_kw) * 100, 1)
                    st.markdown(
                        f'<p style="text-align:center; color:#64748b; font-size:0.88rem; margin-top:-0.5rem;">'
                        f'Out of <b>{total_kw}</b> total keywords, '
                        f'<b style="color:#16a34a">{len(matched)} matched</b> '
                        f'({match_pct}%) and '
                        f'<b style="color:#dc2626">{len(missing)} are missing</b> '
                        f'({round(100 - match_pct, 1)}%).</p>',
                        unsafe_allow_html=True
                    )
            else:
                st.info("No keyword data available to display chart.")

            # =====================================================
            # END PIE CHART
            # =====================================================

            st.markdown("<br>", unsafe_allow_html=True)

            with st.expander("📃 View Extracted Resume Text", expanded=False):
                st.text_area(
                    "Raw Text",
                    value=resume_text if resume_text else "No text extracted.",
                    height=250,
                    disabled=True,
                    label_visibility="collapsed"
                )

        # --------------------------------------------------
        # TAB 2 - CANDIDATE INFO
        # --------------------------------------------------
        with tab2:
            st.markdown('<p class="section-title">Candidate Profile</p>', unsafe_allow_html=True)

            ci1, ci2 = st.columns(2)

            with ci1:
                st.markdown(f"""
                    <div class="info-card">
                        <div class="label">👤 Full Name</div>
                        <div class="value">{candidate_name}</div>
                    </div>
                    <div class="info-card">
                        <div class="label">📧 Email Address</div>
                        <div class="value">{candidate_email}</div>
                    </div>
                """, unsafe_allow_html=True)

            with ci2:
                st.markdown(f"""
                    <div class="info-card">
                        <div class="label">📱 Phone Number</div>
                        <div class="value">{candidate_phone}</div>
                    </div>
                    <div class="info-card">
                        <div class="label">💼 Experience</div>
                        <div class="value">{candidate_experience}</div>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<p class="section-title">Candidate Summary</p>', unsafe_allow_html=True)

            summary_col1, summary_col2, summary_col3 = st.columns(3)
            with summary_col1:
                st.markdown(
                    f'<div class="metric-card"><div class="metric-num">{score}%</div>'
                    f'<div class="metric-lbl">Overall Score</div></div>',
                    unsafe_allow_html=True
                )
            with summary_col2:
                st.markdown(
                    f'<div class="metric-card"><div class="metric-num" style="color:#16a34a">{len(matched)}</div>'
                    f'<div class="metric-lbl">Skills Matched</div></div>',
                    unsafe_allow_html=True
                )
            with summary_col3:
                status = "✅ Shortlisted" if is_shortlisted else "⏳ Not Shortlisted"
                color  = "#16a34a" if is_shortlisted else "#64748b"
                st.markdown(
                    f'<div class="metric-card"><div style="color:{color}; font-size:1.2rem; font-weight:700; margin-top:0.25rem">{status}</div>'
                    f'<div class="metric-lbl">Status</div></div>',
                    unsafe_allow_html=True
                )

        # --------------------------------------------------
        # TAB 3 - AI FEEDBACK
        # --------------------------------------------------
        with tab3:

            feedback_status = feedback.get("status") if isinstance(feedback, dict) else None
            is_invalid      = feedback_status in ("invalid", "error")
            is_valid_result = isinstance(feedback, dict) and not is_invalid

            # ── Case 1: invalid file or non-resume ───────────
            if is_invalid:
                icon = "🤖" if feedback_status == "invalid" else "⚠️"
                st.markdown(
                    f'<div class="feedback-box">'
                    f'{icon} {feedback.get("message", "An unexpected error occurred. Please try again.")}'
                    f'</div>',
                    unsafe_allow_html=True
                )

            # ── Case 2: valid resume — full analysis ─────────
            elif is_valid_result:

                st.markdown('<p class="section-title">AI Analysis</p>', unsafe_allow_html=True)

                fa1, fa2 = st.columns(2)
                with fa1:
                    st.markdown(
                        f'<div class="metric-card"><div class="metric-num">'
                        f'{feedback.get("resume_score", score)}%</div>'
                        f'<div class="metric-lbl">AI Score</div></div>',
                        unsafe_allow_html=True
                    )
                with fa2:
                    st.markdown(
                        f'<div class="metric-card"><div class="metric-num" style="color:#0ea5e9">'
                        f'{len(feedback.get("matched_skills", []))}</div>'
                        f'<div class="metric-lbl">Skills Found</div></div>',
                        unsafe_allow_html=True
                    )

                st.markdown("<br>", unsafe_allow_html=True)

                with st.expander("📌 Professional Feedback", expanded=True):
                    st.markdown(
                        f'<div class="feedback-box">'
                        f'{feedback.get("professional_feedback", "No feedback available.")}'
                        f'</div>',
                        unsafe_allow_html=True
                    )

                with st.expander("🎯 Candidate Suitability", expanded=True):
                    st.markdown(
                        f'<div class="suitability-box">'
                        f'{feedback.get("candidate_suitability", "No suitability analysis available.")}'
                        f'</div>',
                        unsafe_allow_html=True
                    )

                with st.expander("💡 Improvement Suggestions", expanded=True):
                    suggestions = feedback.get("suggestions", [])
                    if suggestions:
                        for suggestion in suggestions:
                            st.markdown(
                                f'<div class="suggestion-item">▸ {suggestion}</div>',
                                unsafe_allow_html=True
                            )
                    else:
                        st.info("No suggestions available.")

            # ── Case 3: plain string fallback ────────────────
            else:
                st.markdown(
                    f'<div class="feedback-box">{feedback}</div>',
                    unsafe_allow_html=True
                )

        # =====================================================
        # SHORTLIST TRACKING
        # =====================================================
        if is_shortlisted:
            shortlisted_candidates.append({
                "Resume Name":    uploaded_file.name,
                "Candidate Name": candidate_name,
                "Score":          score,
                "Email":          candidate_email,
            })

        results.append({
            "Resume Name":      uploaded_file.name,
            "Candidate Name":   candidate_name,
            "Score":            score if not empty_resume else 0,
            "Matched Keywords": len(matched) if not empty_resume else 0,
            "Missing Keywords": len(missing) if not empty_resume else 0,
            "Status":           "Shortlisted" if is_shortlisted else "Not Shortlisted",
        })

    # =====================================================
    # FINAL SUMMARY
    # =====================================================
    if not any_valid_resume_processed:
        st.markdown("<hr class='styled-divider'>", unsafe_allow_html=True)
        st.error(
            "⚠️ None of the uploaded files could be recognized as a resume. "
            "Please upload a valid resume or CV in PDF or DOCX format."
        )
        st.stop()

    if not results:
        st.stop()

    st.markdown("<hr class='styled-divider'>", unsafe_allow_html=True)
    st.success("✅ Resume analysis completed successfully!")

    df = pd.DataFrame(results)
    df = df.sort_values(by="Score", ascending=False).reset_index(drop=True)
    df.insert(0, "Rank", range(1, len(df) + 1))

    # =====================================================
    # LEADERBOARD + BARCHART + TABLE (only if 2+ valid resumes)
    # =====================================================
    if len(results) > 1:

        st.markdown("<br>", unsafe_allow_html=True)

        # LEADERBOARD
        st.markdown("""
            <div style="background:linear-gradient(135deg,#0f172a,#1e3a5f);
                        border-radius:16px; padding:1.5rem 2rem; margin-bottom:1.5rem;">
                <h2 style="color:#facc15; margin:0 0 1rem 0; font-size:1.5rem;">
                    🏆 Candidate Leaderboard
                </h2>
        """, unsafe_allow_html=True)

        rank_medals = {1: "🥇", 2: "🥈", 3: "🥉"}

        for _, row in df.iterrows():
            rank    = int(row["Rank"])
            name    = row["Candidate Name"] if row["Candidate Name"] != "Not Found" else row["Resume Name"]
            score_v = row["Score"]
            medal   = rank_medals.get(rank, f"#{rank}")
            fill    = min(int(score_v), 100)

            if score_v >= 80:
                bar_color   = "#22c55e"
                text_color  = "#4ade80"
                status_pill = '<span style="background:#166534;color:#bbf7d0;padding:2px 10px;border-radius:999px;font-size:0.75rem;font-weight:700;">✅ Shortlisted</span>'
            elif score_v >= 60:
                bar_color   = "#f59e0b"
                text_color  = "#fcd34d"
                status_pill = '<span style="background:#78350f;color:#fde68a;padding:2px 10px;border-radius:999px;font-size:0.75rem;font-weight:700;">👍 Good</span>'
            else:
                bar_color   = "#ef4444"
                text_color  = "#fca5a5"
                status_pill = '<span style="background:#7f1d1d;color:#fecaca;padding:2px 10px;border-radius:999px;font-size:0.75rem;font-weight:700;">⚠️ Low</span>'

            st.markdown(f"""
                <div style="background:rgba(255,255,255,0.05); border-radius:12px;
                            padding:1rem 1.25rem; margin-bottom:0.75rem;
                            border:1px solid rgba(255,255,255,0.08);">
                    <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:0.5rem;">
                        <div style="display:flex; align-items:center; gap:0.75rem;">
                            <span style="font-size:1.6rem;">{medal}</span>
                            <div>
                                <div style="color:#000000; font-weight:700; font-size:1rem;">
                                    Rank {rank} — {name}
                                </div>
                                <div style="color:#94a3b8; font-size:0.78rem; margin-top:1px;">
                                    {row['Resume Name']}
                                </div>
                            </div>
                        </div>
                        <div style="display:flex; align-items:center; gap:0.75rem;">
                            {status_pill}
                            <span style="color:{text_color}; font-size:1.4rem; font-weight:900;">{score_v}%</span>
                        </div>
                    </div>
                    <div style="background:rgba(255,255,255,0.1); border-radius:999px; height:8px;">
                        <div style="background:{bar_color}; width:{fill}%; height:8px;
                                    border-radius:999px;"></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # BAR CHART
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            '<p style="font-size:1.1rem; font-weight:700; color:#1e293b; margin-bottom:0.5rem;">'
            '📊 Score Comparison Chart</p>',
            unsafe_allow_html=True
        )

        import plotly.graph_objects as go

        labels = [
            row["Candidate Name"] if row["Candidate Name"] != "Not Found" else row["Resume Name"]
            for _, row in df.iterrows()
        ]
        scores     = df["Score"].tolist()
        ranks      = df["Rank"].tolist()
        bar_colors = ["#22c55e" if s >= 80 else "#f59e0b" if s >= 60 else "#ef4444" for s in scores]

        fig = go.Figure(go.Bar(
            x=labels,
            y=scores,
            marker_color=bar_colors,
            text=[f"Rank #{r}<br>{s}%" for r, s in zip(ranks, scores)],
            textposition="outside",
            textfont=dict(size=13, color="#1e293b"),
            hovertemplate="<b>%{x}</b><br>Score: %{y}%<extra></extra>",
        ))

        fig.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            yaxis=dict(range=[0, 115], title="Score (%)", gridcolor="#f1f5f9", ticksuffix="%"),
            xaxis=dict(title="Candidate"),
            margin=dict(t=40, b=40, l=40, r=40),
            font=dict(family="Segoe UI", size=13),
            showlegend=False,
            bargap=0.35,
        )

        fig.add_hline(
            y=80,
            line_dash="dash",
            line_color="#6366f1",
            line_width=2,
            annotation_text="  Shortlist Threshold (80%)",
            annotation_position="top left",
            annotation_font_color="#6366f1",
            annotation_font_size=12,
        )

        st.plotly_chart(fig, use_container_width=True)

        # COMPARISON TABLE
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            '<p style="font-size:1.1rem; font-weight:700; color:#1e293b; margin-bottom:0.5rem;">'
            '📋 Full Comparison Table</p>',
            unsafe_allow_html=True
        )
        st.dataframe(df, use_container_width=True, hide_index=True)

    # =====================================================
    # SHORTLISTED CANDIDATES
    # =====================================================
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("🏅 Shortlisted Candidates")

    if shortlisted_candidates:
        shortlisted_df = pd.DataFrame(shortlisted_candidates)
        shortlisted_df = shortlisted_df.sort_values(by="Score", ascending=False).reset_index(drop=True)
        shortlisted_df.insert(0, "Rank", range(1, len(shortlisted_df) + 1))
        st.dataframe(shortlisted_df, use_container_width=True, hide_index=True)
    else:
        st.warning("❌ No candidates met the shortlisting threshold (score ≥ 80%)")