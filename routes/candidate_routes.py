"""
routes/candidate_routes.py
--------------------------
Handles: resume upload, ranking trigger, ranking results display.
"""

import os
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, flash, current_app
)
from werkzeug.utils import secure_filename
from database import queries as q
from services.resume_parser import extract_resume_text, parse_resume_fields
from services.ranking_service import run_ranking_for_job

candidate_bp = Blueprint("candidate", __name__)


def _allowed_file(filename: str) -> bool:
    ext = os.path.splitext(filename)[-1].lower().lstrip(".")
    return ext in current_app.config["ALLOWED_EXTENSIONS"]


def _login_required_redirect():
    from functools import wraps
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "recruiter_id" not in session:
                flash("Please log in.", "warning")
                return redirect(url_for("recruiter.login"))
            return f(*args, **kwargs)
        return wrapper
    return decorator


login_required = _login_required_redirect()


# ════════════════════════════════════════════════════════════════
# UPLOAD RESUME
# ════════════════════════════════════════════════════════════════

@candidate_bp.route("/upload-resume/<int:job_id>", methods=["GET", "POST"])
@login_required
def upload_resume(job_id):
    job = q.get_job_by_id(job_id)
    if not job:
        flash("Job not found.", "danger")
        return redirect(url_for("recruiter.dashboard"))

    if request.method == "POST":
        files      = request.files.getlist("resumes")
        errors     = []
        uploaded   = 0

        for file in files:
            if not file or not file.filename:
                continue

            if not _allowed_file(file.filename):
                errors.append(f"'{file.filename}' — unsupported format (use PDF or DOCX).")
                continue

            # ── Save file securely ────────────────────────────────────────
            filename   = secure_filename(file.filename)
            save_path  = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)

            # Avoid name collisions
            base, ext = os.path.splitext(filename)
            counter   = 1
            while os.path.exists(save_path):
                filename  = f"{base}_{counter}{ext}"
                save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
                counter  += 1

            file.save(save_path)

            # ── Extract text ──────────────────────────────────────────────
            try:
                raw_text = extract_resume_text(save_path)
            except Exception as e:
                errors.append(f"'{filename}' — could not extract text: {e}")
                continue

            # ── Auto-extract email/phone from text ────────────────────────
            fields = parse_resume_fields(raw_text)
            name   = request.form.get(f"name_{file.filename}", "").strip()
            name   = name or os.path.splitext(file.filename)[0]  # fallback

            # ── Persist to DB ─────────────────────────────────────────────
            q.insert_candidate(
                name        = name,
                email       = fields.get("email", ""),
                phone       = fields.get("phone", ""),
                resume_file = filename,
                resume_text = raw_text,
            )
            uploaded += 1

        if errors:
            for err in errors:
                flash(err, "warning")
        if uploaded > 0:
            flash(f"{uploaded} resume(s) uploaded successfully.", "success")
            return redirect(url_for("candidate.rank_candidates_view", job_id=job_id))

        return redirect(url_for("candidate.upload_resume", job_id=job_id))

    # GET — show form
    return render_template("upload_resume.html", job=job)


# ════════════════════════════════════════════════════════════════
# RANK CANDIDATES
# ════════════════════════════════════════════════════════════════

@candidate_bp.route("/rank/<int:job_id>", methods=["GET", "POST"])
@login_required
def rank_candidates_view(job_id):
    """
    GET  : Show existing ranking results for a job.
    POST : Re-run the AI ranking for selected candidates.
    """
    job = q.get_job_by_id(job_id)
    if not job:
        flash("Job not found.", "danger")
        return redirect(url_for("recruiter.dashboard"))

    if request.method == "POST":
        # Recruiter selected specific candidates to rank
        selected_ids = request.form.getlist("candidate_ids")
        if not selected_ids:
            flash("Select at least one candidate to rank.", "warning")
            return redirect(url_for("candidate.rank_candidates_view", job_id=job_id))

        try:
            results = run_ranking_for_job(job_id, [int(i) for i in selected_ids])
            flash(f"AI ranking complete for {len(results)} candidate(s).", "success")
        except Exception as e:
            flash(f"Ranking failed: {e}", "danger")

        return redirect(url_for("candidate.rank_candidates_view", job_id=job_id))

    # GET — load saved rankings
    ranked    = q.get_rankings_for_job(job_id)
    all_cands = q.get_all_candidates()

    return render_template(
        "ranking_result.html",
        job=job,
        ranked=ranked,
        all_candidates=all_cands,
    )
