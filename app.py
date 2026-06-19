import os
import sys

# Force Python to explicitly anchor itself to your project directory root
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from flask import Flask, render_template
from config import Config
from database.db import init_db

# 1. Initialize the core Flask application instance
app = Flask(__name__)

# 2. Load settings from your configuration class
app.config.from_object(Config)

# 3. Import and register blueprint routing modules
from routes.recruiter_routes import recruiter_bp
from routes.candidate_routes import candidate_bp

app.register_blueprint(recruiter_bp)
app.register_blueprint(candidate_bp)

# Base route to render index/home page if needed
@app.route('/')
def index():
    return render_template('index.html')

# 4. Global application execution block
if __name__ == '__main__':
    try:
        # Run database initialization pipeline
        init_db()
        
        print("[DEBUG] Starting local development server on port 5000...", flush=True)
        
        # Use config settings for flexibility
        app.run(host='0.0.0.0', port=5000, debug=Config.DEBUG)
    except Exception as run_err:
        print(f"\nFATAL SERVER LIFECYCLE RUNTIME ERROR: {run_err}", file=sys.stderr)