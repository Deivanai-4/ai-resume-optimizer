import os
import tempfile
from dotenv import load_dotenv

load_dotenv()

def _is_serverless():
    return bool(
        os.environ.get('VERCEL')
        or os.environ.get('VERCEL_ENV')
        or os.environ.get('LAMBDA_TASK_ROOT')
        or os.environ.get('AWS_LAMBDA_FUNCTION_NAME')
        or os.path.dirname(os.path.abspath(__file__)).startswith('/var/task')
    )

IS_SERVERLESS = _is_serverless()

class Config:
    # Must be set via the SECRET_KEY environment variable on every deployment.
    # An empty or missing value will cause Flask session writes to fail at runtime.
    SECRET_KEY = os.environ.get('SECRET_KEY')  # No fallback — must be set in env
    # MySQL Configuration
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_NAME = os.environ.get('DB_NAME', 'ai_career')
    DB_SSL_CA = os.environ.get('DB_SSL_CA', '')
    
    # File Upload: in serverless environments, point UPLOAD_FOLDER to writable /tmp
    if IS_SERVERLESS:
        UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), 'uploads')
    else:
        UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')

    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB
    ALLOWED_RESUME_EXTENSIONS = {'pdf', 'docx', 'doc'}
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # Cloudinary Configuration
    CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME', '')
    CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY', '')
    CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET', '')
    
    # Hugging Face / Qwen — both HF_* and QWEN_* naming conventions are supported
    HF_TOKEN    = os.environ.get('HF_TOKEN',    '')
    HF_PROVIDER = os.environ.get('HF_PROVIDER', 'together')
    HF_MODEL    = os.environ.get('HF_MODEL',    'Qwen/Qwen2.5-7B-Instruct')

    # QWEN_* aliases (preferred going forward — override HF_* if set)
    QWEN_TOKEN    = os.environ.get('QWEN_TOKEN',    '') or HF_TOKEN
    QWEN_PROVIDER = os.environ.get('QWEN_PROVIDER', '') or HF_PROVIDER
    QWEN_MODEL    = os.environ.get('QWEN_MODEL',    '') or HF_MODEL
    QWEN_TIMEOUT  = int(os.environ.get('QWEN_TIMEOUT', 90))
    
    # Session
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PROPAGATE_EXCEPTIONS = True


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
