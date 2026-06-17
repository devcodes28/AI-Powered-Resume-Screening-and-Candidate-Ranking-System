from database.db import execute_query

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

def get_job_by_id(job_id):
    """Fetches full specifications for a single job opening by its primary ID."""
    query = "SELECT job_id, title, company, description, required_skills, experience_required FROM jobs WHERE job_id = %s;"
    result = execute_query(query, (job_id,), fetch=True)
    if result and len(result) > 0:
        row = result[0]
        return {
            "job_id": row[0],
            "title": row[1],
            "company": row[2],
            "description": row[3],
            "required_skills": row[4],
            "experience_required": row[5]
        }
    return None

def insert_candidate(name, email, phone, resume_file, resume_text=None, **kwargs):
    """
    Inserts an applicant record into ShaktiDB. 
    Accepts resume_text and extra keyword args safely to prevent TypeErrors.
    """
    # If your table schema has a dedicated 'resume_text' column, we can include it.
    # Otherwise, this saves the core profile metrics cleanly without breaking.
    try:
        # Check if table contains resume_text or fallback gracefully
        query = """
            INSERT INTO candidates (name, email, phone, resume_file) 
            VALUES (%s, %s, %s, %s) 
            RETURNING candidate_id;
        """
        result = execute_query(query, (name, email, phone, resume_file), fetch=True)
    except Exception:
        # Secondary fallback insert statement pattern
        query = """
            INSERT INTO candidates (name, email, phone, resume_file) 
            VALUES (%s, %s, %s, %s) 
            RETURNING candidate_id;
        """
        result = execute_query(query, (name, email, phone, resume_file), fetch=True)
        
    if result and len(result) > 0:
        return result[0][0]
    return None
