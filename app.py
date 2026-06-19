import os
from flask import Flask, redirect, url_for
from config import Config
from database.db import init_db
from routes.recruiter_routes import recruiter_bp
from routes.candidate_routes import candidate_bp

app = Flask(__name__)
app.config.from_object(Config)

# Ensure absolute structural upload matrices match fallback layouts
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
app.config["ALLOWED_EXTENSIONS"] = {'pdf', 'docx', 'txt'}

# Register Structural Blueprints to Core Matrix
app.register_blueprint(recruiter_bp)
app.register_blueprint(candidate_bp)

@app.route('/')
def index():
    return redirect(url_for('recruiter.dashboard'))

if __name__ == "__main__":
    # Initializes database tables safely using IF NOT EXISTS 
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)