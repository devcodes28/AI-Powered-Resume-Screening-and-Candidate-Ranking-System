import os
import sys
import csv
from io import StringIO
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session, Response, jsonify
from werkzeug.utils import secure_filename
import psycopg2
from psycopg2.extras import RealDictCursor
from services.resume_parser import parse_resume
from services.ranking_service import trigger_ai_ranking_pipeline 
from services.text_preprocessing import preprocess_text

candidate_bp = Blueprint("candidate", __name__)

def get_direct_conn():
    return psycopg2.connect(dbname="resume_ai", user="postgres", host="/tmp")

def _allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['pdf', 'docx', 'txt']

def _clean_string(value: str) -> str:
    if not value: return ""
    return str(value).replace("\x00", "").replace("\u0000", "").strip()


# ════════════════════════════════════════════════════════════════
# 1. THE RANKING HUB (With AI Badges)
# ════════════════════════════════════════════════════════════════
@candidate_bp.route("/rank/<int:job_id>", methods=["GET"])
def rank_candidates_view(job_id):
    if "recruiter_id" not in session:
        return redirect(url_for("recruiter.login"))
        
    try:
        conn = get_direct_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Verify job ownership
        cursor.execute("SELECT job_id, title, company, description FROM jobs WHERE job_id = %s AND recruiter_id = %s;", (job_id, session["recruiter_id"]))
        job_rows = cursor.fetchall()
        if not job_rows:
            cursor.close()
            conn.close()
            flash("Job not found or unauthorized access.", "danger")
            return redirect(url_for("recruiter.dashboard"))
            
        job = job_rows[0]

        # Fetch candidates including status and resume_text for the AI badges
        cursor.execute("SELECT candidate_id, name, email, phone, score, status, resume_text FROM candidates WHERE job_id = %s ORDER BY score DESC, candidate_id DESC;", (job_id,))
        ranked = cursor.fetchall() or []
        cursor.close()
        conn.close()

        # Generate "Explainable AI" Badges on the fly
        job_words = set(preprocess_text(str(job['description'])).split())
        for c in ranked:
            res_words = set(preprocess_text(str(c['resume_text'] or "")).split())
            matches = list(job_words.intersection(res_words))
            # Filter for meaningful words (length > 3) and get top 3 longest matches
            matches = [m for m in matches if len(m) > 3]
            matches.sort(key=len, reverse=True)
            c['badges'] = matches[:3]
            c['status'] = c['status'] or 'Pending' # Fallback if empty
        
        return render_template("ranking_result.html", job=job, rankings=ranked)
    except Exception as e:
        print(f"❌ LEADERBOARD VIEW FAILED: {str(e)}", file=sys.stderr)
        flash("Failed to load leaderboard matrix.", "danger")
        return redirect(url_for("recruiter.dashboard"))


# ════════════════════════════════════════════════════════════════
# 2. STATUS UPDATE API (AJAX Toggle)
# ════════════════════════════════════════════════════════════════
@candidate_bp.route("/update-status/<int:candidate_id>", methods=["POST"])
def update_status(candidate_id):
    if "recruiter_id" not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    try:
        new_status = request.json.get('status', 'Pending')
        conn = get_direct_conn()
        cursor = conn.cursor()
        cursor.execute("UPDATE candidates SET status = %s WHERE candidate_id = %s", (new_status, candidate_id))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ════════════════════════════════════════════════════════════════
# 3. EXPORT CSV PIPELINE
# ════════════════════════════════════════════════════════════════
@candidate_bp.route("/export-csv/<int:job_id>")
def export_csv(job_id):
    if "recruiter_id" not in session:
        return redirect(url_for("recruiter.login"))
        
    try:
        conn = get_direct_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT name, email, phone, score, status FROM candidates WHERE job_id = %s ORDER BY score DESC;", (job_id,))
        candidates = cursor.fetchall()
        cursor.close()
        conn.close()

        def generate():
            data = StringIO()
            writer = csv.writer(data)
            writer.writerow(('Candidate Name', 'Email Address', 'Phone Number', 'AI Alignment Score (%)', 'Pipeline Status'))
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)
            
            for c in candidates:
                writer.writerow((c['name'], c['email'], c['phone'], f"{c['score']}%", c['status']))
                yield data.getvalue()
                data.seek(0)
                data.truncate(0)

        response = Response(generate(), mimetype='text/csv')
        response.headers.set("Content-Disposition", "attachment", filename=f"talent_pipeline_job_{job_id}.csv")
        return response
    except Exception as e:
        flash("Failed to generate CSV export.", "danger")
        return redirect(url_for("candidate.rank_candidates_view", job_id=job_id))


# ════════════════════════════════════════════════════════════════
# 4. ADD EXPLICIT CANDIDATE
# ════════════════════════════════════════════════════════════════
@candidate_bp.route("/add-candidate/<int:job_id>", methods=["GET", "POST"])
def add_candidate(job_id):
    if "recruiter_id" not in session:
        return redirect(url_for("recruiter.login"))

    # ... Fetch Job context ...
    try:
        conn = get_direct_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT job_id, title, company FROM jobs WHERE job_id = %s;", (job_id,))
        job_rows = cursor.fetchall()
        cursor.close()
        conn.close()
        if not job_rows: return redirect(url_for("recruiter.dashboard"))
        job = job_rows[0]
    except Exception:
        return redirect(url_for("recruiter.dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "Unknown")
        email = request.form.get("email", "")
        phone = request.form.get("phone", "")
        file = request.files.get('resume')

        if file and _allowed_file(file.filename):
            filename = secure_filename(file.filename)
            os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
            save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
            file.save(save_path)
            
            raw_text = parse_resume(save_path)

            try:
                conn = get_direct_conn()
                cursor = conn.cursor()
                # Status defaults to 'Pending'
                cursor.execute("""
                    INSERT INTO candidates (name, email, phone, resume_file, resume_text, job_id, score, status) 
                    VALUES (%s, %s, %s, %s, %s, %s, 0.00, 'Pending');
                """, (_clean_string(name), _clean_string(email), _clean_string(phone), filename, _clean_string(raw_text), job_id))
                conn.commit()
                cursor.close()
                conn.close()
                
                trigger_ai_ranking_pipeline(job_id)
                flash(f"Candidate added and AI Rankings updated!", "success")
                return redirect(url_for('candidate.rank_candidates_view', job_id=job_id))
                
            except Exception as e:
                flash(f"Database Error: {e}", "danger")
                
    return render_template("upload_resume.html", job=job)

# ════════════════════════════════════════════════════════════════
# 5. PUBLIC CAREERS PAGE (Job Board)
# ════════════════════════════════════════════════════════════════
# ════════════════════════════════════════════════════════════════
# 5. PUBLIC CAREERS PAGE (Global Job Board)
# ════════════════════════════════════════════════════════════════
@candidate_bp.route("/careers", methods=["GET"])
def public_careers():
    try:
        conn = get_direct_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # This query now fetches all jobs from all recruiters
        query = """
            SELECT j.job_id, j.title, j.company, j.experience_required, j.description, r.name as recruiter_name 
            FROM jobs j
            LEFT JOIN recruiters r ON j.recruiter_id = r.recruiter_id
            ORDER BY j.job_id DESC;
        """
        cursor.execute(query)
        jobs = cursor.fetchall() or []
        
        cursor.close()
        conn.close()
        
        return render_template("careers.html", jobs=jobs)
    except Exception as e:
        print(f"❌ CAREERS PAGE ERROR: {str(e)}")
        return "System Error: Could not load job board.", 500

# ════════════════════════════════════════════════════════════════
# 6. APPLY FOR JOB (Public Form)
# ════════════════════════════════════════════════════════════════
@candidate_bp.route("/apply/<int:job_id>", methods=["GET", "POST"])
def apply_job_public(job_id):
    # Fetch job info
    conn = get_direct_conn()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM jobs WHERE job_id = %s;", (job_id,))
    job = cursor.fetchone()
    cursor.close()
    conn.close()

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        file = request.files.get('resume')

        if file and _allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
            file.save(save_path)
            raw_text = parse_resume(save_path)

            conn = get_direct_conn()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO candidates (name, email, phone, resume_file, resume_text, job_id, score, status) 
                VALUES (%s, %s, %s, %s, %s, %s, 0.00, 'Pending');
            """, (name, email, phone, filename, raw_text, job_id))
            conn.commit()
            cursor.close()
            conn.close()
            
            # AUTOMATICALLY RUN AI RANKING IN BACKGROUND
            trigger_ai_ranking_pipeline(job_id)
            
            return render_template("thank_you.html")

    return render_template("apply_job.html", job=job)