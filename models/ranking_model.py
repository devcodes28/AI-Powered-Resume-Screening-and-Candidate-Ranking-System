import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from services.text_preprocessing import preprocess_text

def rank_candidates(job_desc, candidate_profiles):
    """
    Executes structural vector space comparisons using Sklearn TF-IDF matrices.
    Includes normalizers for sparse-vector human language mapping.
    """
    if not candidate_profiles:
        return []
    
    # 1. Clean the job description text natively
    cleaned_job = preprocess_text(str(job_desc))
    
    # 2. Extract and clean all candidate resume strings
    cleaned_resumes = [preprocess_text(str(c['resume_text'])) for c in candidate_profiles]
    
    # 3. Create a combined text pool for the matrix workspace
    corpus = [cleaned_job] + cleaned_resumes
    
    # FIX 1: Turn off IDF. In small batches, IDF punishes matching core skills 
    # if multiple candidates share them (e.g., driving "React" to a 0 weight).
    vectorizer = TfidfVectorizer(stop_words='english', use_idf=False, sublinear_tf=True)
    
    try:
        tfidf_matrix = vectorizer.fit_transform(corpus)
    except ValueError:
        return [{'candidate_id': c['candidate_id'], 'score': 0.0, 'percentage': 0.0, 'rank_position': i+1} for i, c in enumerate(candidate_profiles)]
    
    job_vector = tfidf_matrix[0]
    ranked_results = []
    
    # 4. Extract similarity values for each candidate resume row
    for index, candidate in enumerate(candidate_profiles):
        resume_vector = tfidf_matrix[index + 1]
        
        # Calculate the raw mathematical dot product
        similarity = cosine_similarity(job_vector, resume_vector)[0][0]
        raw_score = float(similarity)
        
        # FIX 2: Apply a Square-Root Normalization Curve.
        # This maps highly sparse text-vector math (0.01 - 0.20) into intuitive 
        # HR grading percentages (e.g., a raw 0.07 maps to a realistic 66%).
        if raw_score > 0.0:
            adjusted_score = (raw_score ** 0.5) * 2.5
        else:
            adjusted_score = 0.0
            
        # Cap at 98% to maintain scoring realism
        final_score = min(0.98, adjusted_score)
        percentage = round(final_score * 100, 2)
        
        ranked_results.append({
            'candidate_id': candidate['candidate_id'],
            'score': final_score,
            'percentage': percentage
        })
        
    # Sort candidates dynamically by their mapped match percentage
    ranked_results.sort(key=lambda x: x['percentage'], reverse=True)
    
    # Assign leaderboard positions
    for rank_idx, record in enumerate(ranked_results):
        record['rank_position'] = rank_idx + 1
        
    return ranked_results