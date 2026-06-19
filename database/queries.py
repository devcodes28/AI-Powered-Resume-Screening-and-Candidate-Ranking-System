from database.db import execute_query

# ════════════════════════════════════════════════════════════════
# RECRUITER QUERIES
# ════════════════════════════════════════════════════════════════

def get_recruiter_by_email(email):
    query = "SELECT recruiter_id, name, email, password_hash FROM recruiters WHERE email = %s;"
    result = execute_query(query, (email,), fetch=True)
    if result and len(result) > 0:
        row = result[0]
        return {
            "recruiter_id": row[0],
            "name": row[1],
            "email": row[2],
            "password_hash": row[3]
        }
    return None

def create_recruiter(name, email, password_hash):
    query = "INSERT INTO recruiters (name, email, password_hash) VALUES (%s, %s, %s);"
    execute_query(query, (name, email, password_hash))


# ════════════════════════════════════════════════════════════════
# JOB QUERIES
# ════════════════════════════════════════════════════════════════

def get_job_by_id(job_id):
    query = "SELECT job_id, title, company, experience_required, description FROM jobs WHERE job_id = %s;"
    result = execute_query(query, (job_id,), fetch=True)
    if result and len(result) > 0:
        row = result[0]
        return {
            "job_id": row[0],
            "title": row[1],
            "company": row[2],
            "experience_required": row[3],
            "description": row[4]
        }
    return None


# ════════════════════════════════════════════════════════════════
# CANDIDATE QUERIES
# ════════════════════════════════════════════════════════════════

def insert_candidate(name, email, phone, resume_file, resume_text):
    query = """
        INSERT INTO candidates (name, email, phone, resume_file, resume_text) 
        VALUES (%s, %s, %s, %s, %s);
    """
    execute_query(query, (name, email, phone, resume_file, resume_text))

def get_all_candidates():
    query = "SELECT candidate_id, name, email, phone, resume_file FROM candidates;"
    results = execute_query(query, fetch=True)
    candidates = []
    if results:
        for row in results:
            candidates.append({
                "candidate_id": row[0],
                "name": row[1],
                "email": row[2],
                "phone": row[3],
                "resume_file": row[4]
            })
    return candidates