import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    # Database URI Configuration
    # Defaults to SQLite for zero-config stability, or MySQL if specified in DATABASE_URL
    _db_url = os.environ.get('DATABASE_URL')
    if _db_url and _db_url.startswith('mysql'):
        SQLALCHEMY_DATABASE_URI = _db_url
    else:
        # Default SQLite database path
        _base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(_base_dir, 'prism.db')}"


    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 299,
        'pool_pre_ping': True,
    }
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600

    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@prism.app')

    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB

    ITEMS_PER_PAGE = 12


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    WTF_CSRF_TIME_LIMIT = 7200


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
