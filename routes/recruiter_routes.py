from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import psycopg2
from psycopg2.extras import RealDictCursor
import sys

recruiter_bp = Blueprint("recruiter", __name__)

def get_direct_conn():
    """
    Establishes a direct connection using the explicit /tmp UNIX socket 
    directory where your PostgreSQL server is running.
    """
    return psycopg2.connect(
        dbname="resume_ai",
        user="postgres",
        host="/tmp"  # Forces psycopg2 to look in /tmp/.s.PGSQL.5432
    )

@recruiter_bp.route("/dashboard")
def dashboard():
    if "recruiter_id" not in session:
        session["recruiter_id"] = 1
        session["name"] = "Lead Recruiter"

    jobs_list = []
    candidates_list = []

    try:
        # Open direct connection with a Dictionary Cursor so fields match your HTML perfectly
        conn = get_direct_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Fetch Jobs
        cursor.execute("SELECT job_id, title, company, description, required_skills, experience_required FROM jobs ORDER BY job_id DESC;")
        jobs_list = cursor.fetchall() or []
        
        # FIX: Only fetch candidates actively tied to an existing job opening
        cursor.execute("SELECT candidate_id, name, email, phone, score, job_id FROM candidates WHERE job_id IS NOT NULL;")
        candidates_list = cursor.fetchall() or []
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ DIRECT DASHBOARD FETCH FAILED: {str(e)}", file=sys.stderr)
        flash(f"Database sync failed: {str(e)}", "danger")

    return render_template(
        "dashboard.html", 
        jobs=jobs_list, 
        jobs_count=len(jobs_list), 
        resumes_count=len(candidates_list)
    )

@recruiter_bp.route("/add-job", methods=["GET", "POST"])
def add_job():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        company = request.form.get("company", "").strip()
        experience = request.form.get("experience_required", "").strip()
        skills = request.form.get("required_skills", "").strip()
        description = request.form.get("description", "").strip()

        if not (title and company and description):
            flash("Please fill in all required job fields.", "warning")
            return redirect(url_for("recruiter.add_job"))

        try:
            conn = get_direct_conn()
            cursor = conn.cursor()
            
            query = """
                INSERT INTO jobs (title, company, experience_required, required_skills, description) 
                VALUES (%s, %s, %s, %s, %s);
            """
            cursor.execute(query, (title, company, experience, skills, description))
            
            # FORCE COMMIT right here to write directly to your database disk space
            conn.commit()
            cursor.close()
            conn.close()
            
            flash("Job position added successfully to the database matrix.", "success")
            return redirect(url_for("recruiter.dashboard"))
            
        except Exception as e:
            print(f"❌ DIRECT JOB INSERT FAILED: {str(e)}", file=sys.stderr)
            flash(f"Failed to save job posting: {str(e)}", "danger")
            return redirect(url_for("recruiter.add_job"))

    return render_template("add_job.html")

@recruiter_bp.route("/delete-job/<int:job_id>", methods=["POST"])
def delete_job(job_id):
    try:
        conn = get_direct_conn()
        cursor = conn.cursor()
        
        # This single execution deletes the job. PostgreSQL drops associated candidates automatically!
        cursor.execute("DELETE FROM jobs WHERE job_id = %s;", (job_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash("Job posting and all associated candidate records permanently removed.", "success")
    except Exception as e:
        print(f"❌ JOB DELETION FAILED: {str(e)}", file=sys.stderr)
        flash(f"Failed to delete job posting: {str(e)}", "danger")
        
    return redirect(url_for("recruiter.dashboard"))