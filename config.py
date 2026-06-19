import os;
class Config:
    # Flask Parameters
    SECRET_KEY = os.environ.get('SECRET_KEY', 'shakti_secret_key_9921')
    DEBUG = True
    
    # Core Application File Matrices
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Max 16MB file size
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
    
    # ShaktiDB PostgreSQL Database Matrices
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '5432')
    DB_NAME = os.environ.get('DB_NAME', 'resume_ai')
    DB_USER = os.environ.get('DB_USER', 'postgres')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'postgres')