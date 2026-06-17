import sys
from database.db import get_db_connection

def trigger_ai_ranking_pipeline(job_id):
    """
    Simulates or executes the AI matching pipeline between candidate resumes 
    and the required job description metrics inside ShaktiDB.
    """
    print(f"[AI PIPELINE] Initializing ranking engine loop for Job ID: {job_id}...", flush=True)
    
    conn = get_db_connection()
    if not conn:
        print("[AI PIPELINE] Error: Could not connect to ShaktiDB database service.", file=sys.stderr)
        return False
        
    try:
        cursor = conn.cursor()
        
        # 1. Fetch the specifications for the targeted job opening
        cursor.execute("SELECT title, required_skills FROM jobs WHERE job_id = %s", (job_id,))
        job = cursor.fetchone()
        if not job:
            print(f"[AI PIPELINE] Error: Job ID {job_id} not found.", file=sys.stderr)
            return False
            
        # 2. Get all available candidates to compute scores against
        cursor.execute("SELECT candidate_id, resume_file FROM candidates")
        candidates = cursor.fetchall()
        
        if not candidates:
            print("[AI PIPELINE] Notice: No candidates currently registered in system to evaluate.", flush=True)
            return True

        # 3. Clear old rankings for this job layout to prevent unique key violations
        cursor.execute("DELETE FROM rankings WHERE job_id = %s", (job_id,))
        
        # 4. Generate simulated mock AI similarity matching weights for candidates
        import random
        scores = []
        for index, candidate in enumerate(candidates):
            cand_id = candidate[0]
            sim_score = round(random.uniform(0.65, 0.98), 4) 
            pct_match = round(sim_score * 100, 1)
            scores.append((job_id, cand_id, sim_score, pct_match))
            
        # Sort by best matching similarity score
        scores.sort(key=lambda x: x[2], reverse=True)
        
        # 5. Insert rankings with structural position numbers into ShaktiDB
        for rank_pos, score_data in enumerate(scores, start=1):
            cursor.execute("""
                INSERT INTO rankings (job_id, candidate_id, rank_position, similarity_score, percentage_match)
                VALUES (%s, %s, %s, %s, %s)
            """, (score_data[0], score_data[1], rank_pos, score_data[2], score_data[3]))
            
        conn.commit()
        print(f"[+] [AI PIPELINE] Clean processing loop complete. Ranked {len(scores)} candidates seamlessly.", flush=True)
        return True
        
    except Exception as e:
        print(f"[AI PIPELINE] System Exception encountered during compute sequence: {e}", file=sys.stderr)
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

# Alias link mapping so that candidate_routes.py finds its expected import cleanly!
run_ranking_for_job = trigger_ai_ranking_pipeline
