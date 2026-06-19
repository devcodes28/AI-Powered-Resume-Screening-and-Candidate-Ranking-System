-- 1. Jobs Table
CREATE TABLE IF NOT EXISTS jobs (
    job_id SERIAL PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    company VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    required_skills TEXT NOT NULL,
    experience_required VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Candidates Table
CREATE TABLE IF NOT EXISTS candidates (
    candidate_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL,
    phone VARCHAR(30),
    resume_file VARCHAR(255) NOT NULL,
    resume_text TEXT NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. AI Rankings Table
CREATE TABLE IF NOT EXISTS rankings (
    ranking_id SERIAL PRIMARY KEY,
    job_id INT REFERENCES jobs(job_id) ON DELETE CASCADE,
    candidate_id INT REFERENCES candidates(candidate_id) ON DELETE CASCADE,
    similarity_score NUMERIC(5, 4) NOT NULL,
    percentage_match NUMERIC(5, 2) NOT NULL,
    rank_position INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_job_candidate UNIQUE (job_id, candidate_id)
);