from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import psycopg2
from psycopg2.extras import RealDictCursor
import sys
from werkzeug.security import generate_password_hash, check_password_hash

recruiter_bp = Blueprint("recruiter", __name__)

def get_direct_conn():
    """Establishes a direct connection using the explicit /tmp UNIX socket."""
    return psycopg2.connect(
        dbname="resume_ai",
        user="postgres",
        host="/tmp"
    )

# ════════════════════════════════════════════════════════════════
# CORE DASHBOARD & JOB ROUTES
# ════════════════════════════════════════════════════════════════

@recruiter_bp.route("/dashboard")
def dashboard():
    # Security: Ensure user is logged in
    if "recruiter_id" not in session:
        flash("Unauthorized access. Please log in first.", "danger")
        return redirect(url_for("recruiter.login"))

    current_recruiter_id = session["recruiter_id"]
    jobs_list = []
    candidates_list = []

    try:
        conn = get_direct_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # FIX: Only fetch jobs belonging to the currently logged-in recruiter
        cursor.execute("""
            SELECT job_id, title, company, description, required_skills, experience_required 
            FROM jobs 
            WHERE recruiter_id = %s 
            ORDER BY job_id DESC;
        """, (current_recruiter_id,))
        jobs_list = cursor.fetchall() or []
        
        # FIX: Only fetch candidates who applied to jobs owned by this recruiter
        cursor.execute("""
            SELECT c.candidate_id, c.name, c.email, c.phone, c.score, c.job_id 
            FROM candidates c
            JOIN jobs j ON c.job_id = j.job_id
            WHERE j.recruiter_id = %s;
        """, (current_recruiter_id,))
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
    if "recruiter_id" not in session:
        flash("Unauthorized access. Please log in first.", "danger")
        return redirect(url_for("recruiter.login"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        company = request.form.get("company", "").strip()
        experience = request.form.get("experience_required", "").strip()
        skills = request.form.get("required_skills", "").strip()
        description = request.form.get("description", "").strip()
        assessment_url = request.form.get("assessment_url", "").strip()
        # Get the ID of the recruiter making the request
        recruiter_id = session["recruiter_id"]

        if not (title and company and description):
            flash("Please fill in all required job fields.", "danger")
            return redirect(url_for("recruiter.add_job"))

        try:
            conn = get_direct_conn()
            cursor = conn.cursor()
            
            # FIX: Insert the recruiter_id into the database alongside the job info
            query = """
                INSERT INTO jobs (recruiter_id, title, company, experience_required, required_skills, description, assessment_url) 
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """
            cursor.execute(query, (recruiter_id, title, company, experience, skills, description, assessment_url))
            conn.commit()
            cursor.close()
            conn.close()
            
            flash("Job position added successfully to your private matrix.", "success")
            return redirect(url_for("recruiter.dashboard"))
            
        except Exception as e:
            print(f"❌ DIRECT JOB INSERT FAILED: {str(e)}", file=sys.stderr)
            flash(f"Failed to save job posting: {str(e)}", "danger")
            return redirect(url_for("recruiter.add_job"))

    return render_template("add_job.html")

@recruiter_bp.route("/delete-job/<int:job_id>", methods=["POST"])
def delete_job(job_id):
    # Security: Ensure user is logged in
    if "recruiter_id" not in session:
        flash("Unauthorized access. Please log in first.", "danger")
        return redirect(url_for("recruiter.login"))

    recruiter_id = session["recruiter_id"]

    try:
        conn = get_direct_conn()
        cursor = conn.cursor()
        
        # Security: Only delete the job if it belongs to the logged-in recruiter
        cursor.execute("DELETE FROM jobs WHERE job_id = %s AND recruiter_id = %s;", (job_id, recruiter_id))
        
        # Check if the deletion actually happened (in case they tried to delete someone else's job)
        if cursor.rowcount == 0:
            flash("Job not found or you do not have permission to delete it.", "warning")
        else:
            flash("Job posting and all associated candidate records permanently removed.", "success")
            
        conn.commit()
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ JOB DELETION FAILED: {str(e)}", file=sys.stderr)
        flash("Failed to delete job posting.", "danger")
        
    return redirect(url_for("recruiter.dashboard"))

# ════════════════════════════════════════════════════════════════
# SECURE AUTHENTICATION ROUTES
# ════════════════════════════════════════════════════════════════

@recruiter_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        try:
            conn = get_direct_conn()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Look up the recruiter by email
            cursor.execute("SELECT recruiter_id, name, password_hash FROM recruiters WHERE email = %s;", (email,))
            recruiter = cursor.fetchone()
            
            cursor.close()
            conn.close()

            # Verify the recruiter exists AND the password matches the hash
            if recruiter and check_password_hash(recruiter['password_hash'], password):
                session.clear() # Prevent session fixation attacks
                session["recruiter_id"] = recruiter['recruiter_id']
                session["name"] = recruiter['name']
                
                flash("Authentication successful. Welcome to the Neural Console.", "success")
                return redirect(url_for("recruiter.dashboard"))
            else:
                flash("Invalid email or password. Access denied.", "danger")
                
        except Exception as e:
            print(f"❌ LOGIN VERIFICATION ERROR: {str(e)}", file=sys.stderr)
            flash("An internal database error occurred during login.", "danger")

    return render_template("login.html")

@recruiter_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not (name and email and password):
            flash("All fields are required to initialize an account.", "danger")
            return redirect(url_for("recruiter.register"))

        # Cryptographically hash the password before saving to DB
        hashed_pwd = generate_password_hash(password)

        try:
            conn = get_direct_conn()
            cursor = conn.cursor()
            
            # Check if email is already registered
            cursor.execute("SELECT email FROM recruiters WHERE email = %s;", (email,))
            if cursor.fetchone():
                cursor.close()
                conn.close()
                flash("This email is already registered. Please log in.", "warning")
                return redirect(url_for("recruiter.login"))

            # Insert new secure record
            cursor.execute(
                "INSERT INTO recruiters (name, email, password_hash) VALUES (%s, %s, %s);", 
                (name, email, hashed_pwd)
            )
            
            conn.commit()
            cursor.close()
            conn.close()
            
            flash("Profile securely initialized! Please log in with your new credentials.", "success")
            return redirect(url_for("recruiter.login"))
            
        except Exception as e:
            print(f"❌ REGISTRATION INSERT ERROR: {str(e)}", file=sys.stderr)
            flash("Database error occurred during registration.", "danger")
            
    return render_template("register.html")

@recruiter_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        # In a production environment, this would generate a secure token and send an email via SMTP.
        # For now, it gracefully accepts the request to prevent email enumeration.
        flash("If that email exists in our system, a password reset link has been sent.", "success")
        return redirect(url_for("recruiter.login"))
    return render_template("forgot_password.html")

@recruiter_bp.route("/logout")
def logout():
    session.clear()
    flash("Session terminated. You have been securely logged out.", "success")
    return redirect(url_for("recruiter.login"))