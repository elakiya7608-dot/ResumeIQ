from resume import extract_text_from_pdf
from keywords import get_keywords
from scorer import extract_keywords, calculate_score
from api_helper import get_ai_feedback


def main():
    print("\n AI Resume Analyzer Started...\n")

    
    file_path = "resume3.pdf"
    resume_text = extract_text_from_pdf(file_path)

    if not resume_text:
        print("❌ Failed to read resume.")
        return

    print("✅ Resume text extracted\n")


    keywords = get_keywords()

    
    matched, missing = extract_keywords(resume_text,keywords)

    print("✅ Keyword matching done")
    print("Matched Skills:", matched)
    print("Missing Skills:", missing, "\n")

    
    score = calculate_score(matched, keywords)

    print(f"📊 Resume Score: {score}%\n")

    
    print("🤖 Generating AI Feedback...\n")

    feedback = get_ai_feedback(resume_text, matched, score)

    print("📝 AI Feedback:\n")
    print(feedback)


if __name__ == "__main__":
    main()



