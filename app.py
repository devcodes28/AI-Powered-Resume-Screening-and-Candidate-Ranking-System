"""
app.py
------
Flask application factory and entry point.

Run locally:
    python app.py

Production:
    gunicorn -w 4 -b 0.0.0.0:5000 app:app
"""

import os
from flask import Flask
from config import Config
from routes.recruiter_routes import recruiter_bp
from routes.candidate_routes import candidate_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    # ── Ensure upload directory exists ────────────────────────────────────
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # ── Register Blueprints ───────────────────────────────────────────────
    app.register_blueprint(recruiter_bp)   # /, /login, /dashboard, /add-job …
    app.register_blueprint(candidate_bp)   # /upload-resume, /rank/<id> …

    # ── Global template context ───────────────────────────────────────────
    @app.context_processor
    def inject_globals():
        from flask import session
        return {
            "app_name": "ResumeAI",
            "recruiter_name": session.get("recruiter_name", ""),
        }

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=Config.DEBUG, host="0.0.0.0", port=5000)
