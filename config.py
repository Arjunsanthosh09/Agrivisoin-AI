import os
from dotenv import load_dotenv
load_dotenv()
class Config:
    # Flask
    SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-change-this-in-production")
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
    GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
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
    
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # Point directly to the 'color' folder
    DISEASE_DATASET_PATH = os.path.join(BASE_DIR, 'data', 'datasets', 'disease_dataset', 'color')