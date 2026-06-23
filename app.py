import os
# Added 'session' and 'render_template' to the imports
from flask import Flask, redirect, url_for, render_template, session
from config import Config
from database.db import init_db
from routes.recruiter_routes import recruiter_bp
from routes.candidate_routes import candidate_bp

app = Flask(__name__)
app.config.from_object(Config)

app.config["UPLOAD_FOLDER"] = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
app.config["ALLOWED_EXTENSIONS"] = {'pdf', 'docx', 'txt'}

app.register_blueprint(recruiter_bp)
app.register_blueprint(candidate_bp)

@app.route('/')
def index():
    # SECURITY & UX: If the recruiter is already logged in, skip the landing page
    if 'recruiter_id' in session:
        return redirect(url_for('recruiter.dashboard'))
    
    return render_template('index.html')

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)