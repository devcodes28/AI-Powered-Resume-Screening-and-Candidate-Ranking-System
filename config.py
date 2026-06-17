import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'shakti_ai_secret_super_key_12345')
    
    # ShaktiDB Configuration (PostgreSQL Compatible Connection String)
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '5432')
    DB_NAME = os.environ.get('DB_NAME', 'resume_ai')
    DB_USER = os.environ.get('DB_USER', 'postgres')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'postgres')
    
    # File Upload Settings
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads/resumes')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB Max Upload Limit
    ALLOWED_EXTENSIONS = {'pdf', 'docx'}
    DEBUG = True
