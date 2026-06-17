"""
services/text_preprocessing.py
--------------------------------
NLP pipeline for cleaning raw text before TF-IDF vectorisation.

Pipeline
--------
1. Lowercase
2. Remove URLs & email addresses
3. Remove punctuation & digits
4. Tokenise
5. Remove stopwords
6. Lemmatise (reduces words to root form, e.g. "running" → "run")
7. Rejoin tokens
"""

import re
import string
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

# ── Download required NLTK data once ─────────────────────────────────────────
_REQUIRED = ["punkt", "stopwords", "wordnet", "omw-1.4", "punkt_tab"]
for _pkg in _REQUIRED:
    try:
        nltk.data.find(f"tokenizers/{_pkg}")
    except LookupError:
        nltk.download(_pkg, quiet=True)

_STOP_WORDS  = set(stopwords.words("english"))
_LEMMATIZER  = WordNetLemmatizer()


def preprocess_text(text: str) -> str:
    """
    Full NLP cleaning pipeline.

    Parameters
    ----------
    text : raw string (resume text or job description)

    Returns
    -------
    Cleaned, lemmatised string ready for TF-IDF.

    Example
    -------
    >>> preprocess_text("Python Developer with Machine Learning Experience!")
    'python developer machine learning experience'
    """
    if not text or not isinstance(text, str):
        return ""

    # 1. Lowercase
    text = text.lower()

    # 2. Remove URLs
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)

    # 3. Remove email addresses
    text = re.sub(r"\S+@\S+", " ", text)

    # 4. Remove punctuation and digits
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\d+", " ", text)

    # 5. Tokenise
    tokens = word_tokenize(text)

    # 6. Remove stopwords and short tokens (single chars)
    tokens = [t for t in tokens if t not in _STOP_WORDS and len(t) > 1]

    # 7. Lemmatise
    tokens = [_LEMMATIZER.lemmatize(t) for t in tokens]

    return " ".join(tokens)


def extract_skills_keywords(text: str, skill_list: list[str] = None) -> list[str]:
    """
    Find known skills/keywords that appear in the text.
    Falls back to the top-30 most frequent tokens if no skill list is given.
    """
    cleaned = preprocess_text(text)
    tokens  = cleaned.split()

    if skill_list:
        found = [s.lower() for s in skill_list if s.lower() in cleaned]
        return list(set(found))

    # Frequency-based fallback
    from collections import Counter
    freq = Counter(tokens)
    return [word for word, _ in freq.most_common(30)]
