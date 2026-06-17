"""
models/ranking_model.py
-----------------------
Core AI ranking engine.

Algorithm
---------
1. Combine the job description + all resume texts into one corpus.
2. Fit a TF-IDF vectoriser on the corpus.
3. Transform every document into a TF-IDF vector.
4. Compute cosine similarity between the job vector (index 0)
   and each resume vector.
5. Return a sorted list of dicts with candidate_id, score, rank.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


def rank_candidates(job_description: str, candidate_resumes: list[dict]) -> list[dict]:
    """
    Rank candidates against a job description using TF-IDF + Cosine Similarity.

    Parameters
    ----------
    job_description : str
        Pre-processed text of the job description.
    candidate_resumes : list of dict
        Each dict must have:
            'candidate_id' : int
            'text'         : str  (pre-processed resume text)

    Returns
    -------
    list of dict, sorted descending by similarity score:
        {
            'candidate_id'    : int,
            'similarity_score': float  (0.0 – 1.0),
            'percentage_match': float  (0.0 – 100.0),
            'rank'            : int    (1-based)
        }
    """

    if not candidate_resumes:
        return []

    # ── Step 1: Build corpus ──────────────────────────────────────────────
    # Index 0 = job description; indexes 1..N = resumes
    corpus = [job_description] + [c["text"] for c in candidate_resumes]

    # ── Step 2: Fit TF-IDF ───────────────────────────────────────────────
    vectoriser = TfidfVectorizer(
        sublinear_tf=True,      # apply log normalization to term frequency
        ngram_range=(1, 2),     # unigrams + bigrams for better phrase matching
        min_df=1,               # keep rare terms (small corpus)
        stop_words="english",   # built-in English stopword removal
    )
    tfidf_matrix = vectoriser.fit_transform(corpus)

    # ── Step 3: Compute cosine similarity ────────────────────────────────
    job_vector    = tfidf_matrix[0:1]          # shape (1, features)
    resume_matrix = tfidf_matrix[1:]           # shape (N, features)

    similarities = cosine_similarity(job_vector, resume_matrix).flatten()
    # similarities[i] corresponds to candidate_resumes[i]

    # ── Step 4: Build result list ─────────────────────────────────────────
    results = []
    for idx, candidate in enumerate(candidate_resumes):
        score = float(similarities[idx])
        results.append(
            {
                "candidate_id"    : candidate["candidate_id"],
                "similarity_score": round(score, 4),
                "percentage_match": round(score * 100, 2),
            }
        )

    # ── Step 5: Sort descending and assign ranks ──────────────────────────
    results.sort(key=lambda x: x["similarity_score"], reverse=True)
    for rank, result in enumerate(results, start=1):
        result["rank"] = rank

    return results


def get_feature_importance(job_description: str, resume_text: str,
                           top_n: int = 10) -> list[dict]:
    """
    Return the top-N TF-IDF features (terms) shared between the job
    description and a single resume — used for the 'matched skills' display.

    Returns
    -------
    list of {'term': str, 'score': float}
    """
    vectoriser = TfidfVectorizer(
        sublinear_tf=True,
        ngram_range=(1, 2),
        stop_words="english",
    )
    matrix = vectoriser.fit_transform([job_description, resume_text])
    feature_names = vectoriser.get_feature_names_out()

    job_vec    = matrix[0].toarray().flatten()
    resume_vec = matrix[1].toarray().flatten()

    # Term must appear in BOTH documents
    shared_mask   = (job_vec > 0) & (resume_vec > 0)
    shared_scores = (job_vec * resume_vec)  # element-wise product as relevance proxy

    top_indices = np.argsort(shared_scores * shared_mask)[::-1][:top_n]
    matched = [
        {"term": feature_names[i], "score": round(float(shared_scores[i]), 4)}
        for i in top_indices
        if shared_mask[i]
    ]
    return matched
