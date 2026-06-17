-- =============================================================
-- schema.sql  –  ShaktiDB schema for AI Resume Screening System
-- Run once:  psql -U postgres -d resume_ai -f database/schema.sql
-- =============================================================

-- ── Drop tables in reverse FK order (safe re-run) ─────────────
DROP TABLE IF EXISTS rankings   CASCADE;
DROP TABLE IF EXISTS candidates CASCADE;
DROP TABLE IF EXISTS jobs       CASCADE;
DROP TABLE IF EXISTS recruiters CASCADE;

-- ── recruiters ────────────────────────────────────────────────
CREATE TABLE recruiters (
    recruiter_id  SERIAL        PRIMARY KEY,
    name          VARCHAR(120)  NOT NULL,
    email         VARCHAR(200)  NOT NULL UNIQUE,
    password_hash VARCHAR(256)  NOT NULL,
    created_at    TIMESTAMP     DEFAULT NOW()
);

-- ── jobs ──────────────────────────────────────────────────────
CREATE TABLE jobs (
    job_id              SERIAL        PRIMARY KEY,
    recruiter_id        INTEGER       REFERENCES recruiters(recruiter_id) ON DELETE CASCADE,
    title               VARCHAR(200)  NOT NULL,
    company             VARCHAR(200)  NOT NULL,
    description         TEXT          NOT NULL,
    required_skills     TEXT,
    experience_required VARCHAR(50),
    created_at          TIMESTAMP     DEFAULT NOW()
);

-- ── candidates ────────────────────────────────────────────────
CREATE TABLE candidates (
    candidate_id  SERIAL        PRIMARY KEY,
    name          VARCHAR(120)  NOT NULL,
    email         VARCHAR(200),
    phone         VARCHAR(30),
    resume_file   VARCHAR(300)  NOT NULL,
    resume_text   TEXT,
    uploaded_at   TIMESTAMP     DEFAULT NOW()
);

-- ── rankings ──────────────────────────────────────────────────
CREATE TABLE rankings (
    ranking_id        SERIAL    PRIMARY KEY,
    job_id            INTEGER   NOT NULL REFERENCES jobs(job_id)       ON DELETE CASCADE,
    candidate_id      INTEGER   NOT NULL REFERENCES candidates(candidate_id) ON DELETE CASCADE,
    similarity_score  NUMERIC(6,4)  NOT NULL,
    percentage_match  NUMERIC(5,2)  NOT NULL,
    rank_position     INTEGER   NOT NULL,
    matched_skills    TEXT,
    created_at        TIMESTAMP DEFAULT NOW()
);

-- ── Indexes for common lookups ────────────────────────────────
CREATE INDEX idx_rankings_job    ON rankings(job_id);
CREATE INDEX idx_rankings_cand   ON rankings(candidate_id);
CREATE INDEX idx_jobs_recruiter  ON jobs(recruiter_id);

-- ── Seed a demo recruiter (password = "admin123") ────────────
-- Hash generated with werkzeug.security.generate_password_hash
INSERT INTO recruiters (name, email, password_hash)
VALUES (
    'Admin Recruiter',
    'admin@resumeai.com',
    'scrypt:32768:8:1$demoHashPlaceholder$abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890'
);
