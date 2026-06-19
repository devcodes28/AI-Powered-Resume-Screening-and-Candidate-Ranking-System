import os
import sys
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
import psycopg2
from psycopg2.extras import RealDictCursor
from services.resume_parser import parse_resume
from services.ranking_service import trigger_ai_ranking_pipeline 

candidate_bp = Blueprint("candidate", __name__)

def get_direct_conn():
    return psycopg2.connect(
        dbname="resume_ai",
        user="postgres",
        host="/tmp"
    )

def _allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['pdf', 'docx', 'txt']

def _clean_string(value: str) -> str:
    if not value: return ""
    return str(value).replace("\x00", "").replace("\u0000", "").strip()

# ---------------------------------------------------------
# 1. THE RANKING HUB (Pulls Fresh Data Instantly)
# ---------------------------------------------------------
@candidate_bp.route("/rank/<int:job_id>", methods=["GET"])
def rank_candidates_view(job_id):
    try:
        conn = get_direct_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Pull targeted job detail
        cursor.execute("SELECT job_id, title, company, description FROM jobs WHERE job_id = %s;", (job_id,))
        job_rows = cursor.fetchall()
        
        if not job_rows:
            cursor.close()
            conn.close()
            flash("Target position reference missing.", "danger")
            return redirect(url_for("recruiter.dashboard"))
        job = job_rows[0]

        # Fetch candidate rankings sorted by score DESC
        cursor.execute("SELECT candidate_id, name, email, phone, score FROM candidates WHERE job_id = %s ORDER BY score DESC, candidate_id DESC;", (job_id,))
        ranked = cursor.fetchall() or []
        
        cursor.close()
        conn.close()
        
        return render_template("ranking_result.html", job=job, rankings=ranked, ranked=ranked)
    except Exception as e:
        print(f"❌ LEADERBOARD VIEW FAILED: {str(e)}", file=sys.stderr)
        flash(f"Failed to load leaderboard matrix: {str(e)}", "danger")
        return redirect(url_for("recruiter.dashboard"))


# ---------------------------------------------------------
# 2. ADD EXPLICIT CANDIDATE (Runs Pipeline Synchronously)
# ---------------------------------------------------------
@candidate_bp.route("/add-candidate/<int:job_id>", methods=["GET", "POST"])
def add_candidate(job_id):
    try:
        conn = get_direct_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT job_id, title, company FROM jobs WHERE job_id = %s;", (job_id,))
        job_rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not job_rows:
            return redirect(url_for("recruiter.dashboard"))
        job = job_rows[0]
    except Exception as e:
        print(f"❌ FAILED TO FETCH JOB CONTEXT: {str(e)}", file=sys.stderr)
        return redirect(url_for("recruiter.dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "Unknown Candidate")
        email = request.form.get("email", "no-email@example.com")
        phone = request.form.get("phone", "N/A")
        
        if 'resume' not in request.files:
            flash("Please attach the candidate's resume.", "danger")
            return redirect(request.url)
            
        file = request.files['resume']
        if file.filename == '':
            flash("No file selected.", "warning")
            return redirect(request.url)

        if file and _allowed_file(file.filename):
            filename = secure_filename(file.filename)
            os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
            
            save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
            
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(save_path):
                filename = f"{base}_{counter}{ext}"
                save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
                counter += 1

            try:
                file.save(save_path)
                raw_text = parse_resume(save_path)
                
                name = _clean_string(name)
                email = _clean_string(email)
                phone = _clean_string(phone)
                filename = _clean_string(filename)
                raw_text = _clean_string(raw_text)

                # Open Write connection
                conn = get_direct_conn()
                cursor = conn.cursor()
                
                # Insert the candidate record
                insert_query = """
                    INSERT INTO candidates (name, email, phone, resume_file, resume_text, job_id, score) 
                    VALUES (%s, %s, %s, %s, %s, %s, 0.00);
                """
                cursor.execute(insert_query, (name, email, phone, filename, raw_text, job_id))
                
                # Commit candidate immediately so the pipeline can find them in the database
                conn.commit()
                cursor.close()
                conn.close()
                
                # Trigger calculations synchronously
                pipeline_success = trigger_ai_ranking_pipeline(job_id)
                
                if pipeline_success:
                    flash(f"Candidate '{name}' successfully added and AI Rankings updated!", "success")
                else:
                    flash(f"Candidate saved, but AI pipeline returned 0 or failed to compute scores.", "warning")

                return redirect(url_for('candidate.rank_candidates_view', job_id=job_id))
                
            except Exception as e:
                print(f"❌ CANDIDATE INSERT CRASHED: {str(e)}", file=sys.stderr)
                flash(f"Database/System Error: {e}", "danger")
                
    return render_template("upload_resume.html", job=job)