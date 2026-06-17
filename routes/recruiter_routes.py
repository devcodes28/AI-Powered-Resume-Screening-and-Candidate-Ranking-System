from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db_connection
from services.ranking_service import trigger_ai_ranking_pipeline
import database.queries as q
import psycopg2.extras

recruiter_bp = Blueprint('recruiter', __name__)

@recruiter_bp.route("/")
def index():
    if "recruiter_id" in session:
        return redirect(url_for("recruiter.dashboard"))
    return render_template("index.html")

@recruiter_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        recruiter = q.get_recruiter_by_email(email)
        
        if recruiter:
            if isinstance(recruiter, dict):
                p_hash = recruiter.get("password_hash") or recruiter.get("password")
                r_id   = recruiter.get("recruiter_id") or recruiter.get("id")
                r_name = recruiter.get("name")
            else:
                r_id, r_name, _, p_hash = recruiter

            if p_hash and check_password_hash(p_hash, password):
                session["recruiter_id"]   = r_id
                session["recruiter_name"] = r_name
                flash(f"Welcome back, {r_name}!", "success")
                return redirect(url_for("recruiter.dashboard"))

        flash("Invalid email or password.", "danger")
        return redirect(url_for("recruiter.login"))

    return render_template("login.html")

@recruiter_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name     = request.form.get("name", "").strip()
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for("recruiter.register"))

        existing = q.get_recruiter_by_email(email)
        if existing:
            flash("An account with this email already exists.", "warning")
            return redirect(url_for("recruiter.login"))

        hashed_password = generate_password_hash(password)
        try:
            q.create_recruiter(name, email, hashed_password)
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("recruiter.login"))
        except Exception as e:
            flash("Registration failed.", "danger")
            return redirect(url_for("recruiter.register"))

    return render_template("register.html")

@recruiter_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("recruiter.login"))

@recruiter_bp.route('/dashboard')
def dashboard():
    conn = get_db_connection()
    if not conn:
        return "Database Connection Refused", 500
        
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # 1. Fetch total jobs count
    cursor.execute("SELECT COUNT(*) as count FROM jobs")
    total_jobs = cursor.fetchone()['count']
    
    # 2. Fetch total candidates count
    cursor.execute("SELECT COUNT(*) as count FROM candidates")
    total_candidates = cursor.fetchone()['count']
    
    # 3. Fetch total individual rankings completed across the system
    cursor.execute("SELECT COUNT(*) as count FROM rankings")
    total_rankings = cursor.fetchone()['count']
    
    # Package statistics into the structured format expected by dashboard.html
    stats = {
        'total_jobs': total_jobs,
        'total_candidates': total_candidates,
        'total_rankings': total_rankings
    }
    
    # 4. Fetch tracking job openings table matrices
    cursor.execute("SELECT * FROM jobs ORDER BY created_at DESC")
    jobs = cursor.fetchall()
    
    conn.close()
    return render_template('dashboard.html', stats=stats, jobs=jobs)

@recruiter_bp.route('/add-job', methods=['GET', 'POST'])
def add_job():
    if request.method == 'POST':
        title = request.form['title']
        company = request.form['company']
        description = request.form['description']
        required_skills = request.form['required_skills']
        experience_required = request.form['experience_required']
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO jobs (title, company, description, required_skills, experience_required)
                VALUES (%s, %s, %s, %s, %s)
            """, (title, company, description, required_skills, experience_required))
            conn.commit()
            conn.close()
            flash("Job specification stored permanently in ShaktiDB!", "success")
            return redirect(url_for('recruiter.dashboard'))
    return render_template('add_job.html')

@recruiter_bp.route('/delete-job/<int:job_id>', methods=['POST'])
def delete_job(job_id):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM rankings WHERE job_id = %s", (job_id,))
            cursor.execute("DELETE FROM jobs WHERE job_id = %s", (job_id,))
            conn.commit()
            flash("Job specification removed cleanly from ShaktiDB.", "info")
        except Exception as e:
            conn.rollback()
            flash(f"Error purging job profile: {e}", "danger")
        finally:
            conn.close()
    return redirect(url_for('recruiter.dashboard'))

@recruiter_bp.route('/rank/<int:job_id>')
def rank_job_candidates(job_id):
    pipeline_success = trigger_ai_ranking_pipeline(job_id)
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cursor.execute("SELECT * FROM jobs WHERE job_id = %s", (job_id,))
    job = cursor.fetchone()
    
    cursor.execute("SELECT * FROM candidates")
    candidates = cursor.fetchall()
    
    cursor.execute("""
        SELECT r.rank_position, r.similarity_score, r.percentage_match, 
               c.name, c.email, c.phone, c.resume_file, c.candidate_id
        FROM rankings r
        JOIN candidates c ON r.candidate_id = c.candidate_id
        WHERE r.job_id = %s
        ORDER BY r.rank_position ASC
    """, (job_id,))
    rankings = cursor.fetchall()
    
    conn.close()
    
    return render_template(
        'ranking_result.html', 
        job=job, 
        rankings=rankings, 
        candidates=candidates, 
        pipeline_success=pipeline_success
    )
