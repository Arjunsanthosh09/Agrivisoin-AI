import os

class Config:
    # Flask
    SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-change-this-in-production")
    
    # Database - NO PASSWORD (empty string)
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")  # ⬅️ CHANGE THIS TO EMPTY STRING
    DB_NAME = os.environ.get("DB_NAME", "agrivision_ai")
    DB_PORT = int(os.environ.get("DB_PORT", 3306))
    
    # Upload settings
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}