import re

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.stem import PorterStemmer


# =====================================================
# NLP OBJECTS
# =====================================================
lemmatizer = WordNetLemmatizer()
stemmer = PorterStemmer()
stop_words = set(stopwords.words("english"))


# =====================================================
# SYNONYM DICTIONARY
# =====================================================
SYNONYMS = {
    "LLM": ["Large Language Model"],
    "AI": ["Artificial Intelligence"],
    "ML": ["Machine Learning"],
    "NLP": ["Natural Language Processing"],
    "DL": ["Deep Learning"],
    "SQL": ["Structured Query Language"]
}


# =====================================================
# TEXT PREPROCESSING
# =====================================================
def preprocess_text(text):

    # Convert to lowercase
    text = text.lower()

    # Remove punctuation
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)

    # Tokenization
    tokens = word_tokenize(text)

    # Remove stopwords
    tokens = [word for word in tokens if word not in stop_words]

    # Lemmatization
    tokens = [lemmatizer.lemmatize(word) for word in tokens]

    # Stemming
    tokens = [stemmer.stem(word) for word in tokens]

    return tokens


# =====================================================
# KEYWORD EXTRACTION
# =====================================================
def extract_keywords(resume_text, keyword_list):

    matched = []
    missing = []

    resume_text_lower = resume_text.lower()

    resume_tokens = preprocess_text(resume_text)
    resume_set = set(resume_tokens)

    for keyword in keyword_list:

        keyword_found = False

        # -----------------------------------------
        # MULTI-WORD KEYWORDS
        # -----------------------------------------
        if len(keyword.split()) > 1:

            if keyword.lower() in resume_text_lower:
                keyword_found = True

        # -----------------------------------------
        # SINGLE-WORD KEYWORDS
        # -----------------------------------------
        else:

            keyword_tokens = preprocess_text(keyword)

            if keyword_tokens:

                keyword_processed = keyword_tokens[0]

                if keyword_processed in resume_set:
                    keyword_found = True

        # -----------------------------------------
        # SYNONYM CHECK
        # -----------------------------------------
        if not keyword_found:

            keyword_upper = keyword.upper()

            if keyword_upper in SYNONYMS:

                for synonym in SYNONYMS[keyword_upper]:

                    if synonym.lower() in resume_text_lower:
                        keyword_found = True
                        break

        # -----------------------------------------
        # FINAL RESULT
        # -----------------------------------------
        if keyword_found:
            matched.append(keyword)
        else:
            missing.append(keyword)

    return matched, missing


# =====================================================
# SCORE CALCULATION 
# =====================================================
def calculate_score(matched, total):

    if len(total) == 0:
        return 0

    score = (len(matched) / len(total)) * 100

    return round(score, 2)