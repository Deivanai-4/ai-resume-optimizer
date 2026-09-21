import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', '')    
    # MySQL Configuration
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_NAME = os.environ.get('DB_NAME', 'ai_career')
    
    # File Upload
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB
    ALLOWED_RESUME_EXTENSIONS = {'pdf', 'docx', 'doc'}
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # Hugging Face / Qwen — both HF_* and QWEN_* naming conventions are supported
    HF_TOKEN    = os.environ.get('HF_TOKEN',    '')
    HF_PROVIDER = os.environ.get('HF_PROVIDER', 'together')
    HF_MODEL    = os.environ.get('HF_MODEL',    'Qwen/Qwen2.5-7B-Instruct')

    # QWEN_* aliases (preferred going forward — override HF_* if set)
    QWEN_TOKEN    = os.environ.get('QWEN_TOKEN',    '') or HF_TOKEN
    QWEN_PROVIDER = os.environ.get('QWEN_PROVIDER', '') or HF_PROVIDER
    QWEN_MODEL    = os.environ.get('QWEN_MODEL',    '') or HF_MODEL
    
    # Session
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
