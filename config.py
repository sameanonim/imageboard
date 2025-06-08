import os
import secrets
from dotenv import load_dotenv
from datetime import timedelta
from typing import Dict, Any, Optional
from pathlib import Path

load_dotenv()

class Config:
    # Базовые настройки
    SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_hex(32))
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    TESTING = os.getenv('FLASK_TESTING', 'False').lower() == 'true'
    
    # Настройки базы данных
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://imageboard:imageboard@localhost/imageboard')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.getenv('DB_POOL_SIZE', 10)),
        'pool_timeout': int(os.getenv('DB_POOL_TIMEOUT', 30)),
        'pool_recycle': int(os.getenv('DB_POOL_RECYCLE', 3600)),
        'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', 5))
    }
    
    # Настройки Redis
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    REDIS_OPTIONS = {
        'socket_timeout': int(os.getenv('REDIS_TIMEOUT', 5)),
        'socket_connect_timeout': int(os.getenv('REDIS_CONNECT_TIMEOUT', 5)),
        'retry_on_timeout': True,
        'max_connections': int(os.getenv('REDIS_MAX_CONNECTIONS', 10))
    }
    
    # Настройки Celery
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TIMEZONE = 'UTC'
    CELERY_TASK_TRACK_STARTED = True
    CELERY_TASK_TIME_LIMIT = int(os.getenv('CELERY_TASK_TIME_LIMIT', 3600))
    CELERY_TASK_SOFT_TIME_LIMIT = int(os.getenv('CELERY_TASK_SOFT_TIME_LIMIT', 3000))
    
    # Настройки загрузки файлов
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'mp4', 'webm'}
    MAX_FILES_PER_POST = int(os.getenv('MAX_FILES_PER_POST', 4))
    THUMBNAIL_SIZE = (200, 200)
    PREVIEW_SIZE = (800, 800)
    
    # Настройки безопасности
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'True').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=int(os.getenv('SESSION_LIFETIME_DAYS', 7)))
    REMEMBER_COOKIE_DURATION = timedelta(days=int(os.getenv('REMEMBER_COOKIE_DAYS', 30)))
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    
    # Настройки безопасности паролей
    PASSWORD_SALT = os.getenv('PASSWORD_SALT', secrets.token_hex(16))
    PASSWORD_MIN_LENGTH = int(os.getenv('PASSWORD_MIN_LENGTH', 8))
    PASSWORD_REQUIRE_UPPER = True
    PASSWORD_REQUIRE_LOWER = True
    PASSWORD_REQUIRE_DIGITS = True
    PASSWORD_REQUIRE_SPECIAL = True
    
    # Настройки API
    API_RATE_LIMIT = os.getenv('API_RATE_LIMIT', '100/hour')
    API_RATE_LIMIT_STORAGE_URL = REDIS_URL
    
    # Настройки WebSocket
    SOCKET_PING_INTERVAL = int(os.getenv('SOCKET_PING_INTERVAL', 25))
    SOCKET_PING_TIMEOUT = int(os.getenv('SOCKET_PING_TIMEOUT', 120))
    SOCKET_MAX_CONNECTIONS = int(os.getenv('SOCKET_MAX_CONNECTIONS', 1000))
    SOCKETIO_MESSAGE_QUEUE = os.getenv('SOCKETIO_MESSAGE_QUEUE', REDIS_URL)
    SOCKETIO_ASYNC_MODE = os.getenv('SOCKETIO_ASYNC_MODE', 'threading')
    
    # Настройки кэширования
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_TIMEOUT', 300))
    CACHE_KEY_PREFIX = 'imageboard:'
    
    # Настройки логирования
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = os.getenv('LOG_FILE', 'logs/imageboard.log')
    LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', 10 * 1024 * 1024))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', 5))
    
    # Настройки резервного копирования
    BACKUP_FOLDER = os.getenv('BACKUP_FOLDER', 'backups')
    BACKUP_RETENTION_DAYS = int(os.getenv('BACKUP_RETENTION_DAYS', 30))
    BACKUP_SCHEDULE = os.getenv('BACKUP_SCHEDULE', '0 0 * * *')  # Ежедневно в полночь
    
    # Настройки модерации
    MODERATION_QUEUE_SIZE = int(os.getenv('MODERATION_QUEUE_SIZE', 100))
    MODERATION_TIMEOUT = int(os.getenv('MODERATION_TIMEOUT', 3600))  # 1 час
    MODERATION_NOTIFY_ADMINS = os.getenv('MODERATION_NOTIFY_ADMINS', 'True').lower() == 'true'
    
    # Настройки достижений
    ACHIEVEMENTS_ENABLED = os.getenv('ACHIEVEMENTS_ENABLED', 'True').lower() == 'true'
    ACHIEVEMENT_NOTIFICATION_DURATION = int(os.getenv('ACHIEVEMENT_NOTIFICATION_DURATION', 5000))
    
    # Настройки поиска
    SEARCH_INDEX_PATH = os.getenv('SEARCH_INDEX_PATH', 'search_index')
    SEARCH_BATCH_SIZE = int(os.getenv('SEARCH_BATCH_SIZE', 1000))
    SEARCH_MAX_RESULTS = int(os.getenv('SEARCH_MAX_RESULTS', 100))
    
    # Настройки локализации
    LANGUAGES = {
        'ru': 'Русский',
        'en': 'English'
    }
    DEFAULT_LANGUAGE = os.getenv('DEFAULT_LANGUAGE', 'ru')
    BABEL_DEFAULT_LOCALE = DEFAULT_LANGUAGE
    BABEL_DEFAULT_TIMEZONE = 'UTC'
    
    # Настройки темы
    THEME_DEFAULT = os.getenv('THEME_DEFAULT', 'light')
    THEME_COOKIE_NAME = 'theme'
    THEME_COOKIE_DURATION = timedelta(days=365)
    
    @classmethod
    def validate(cls) -> None:
        """Проверка корректности настроек."""
        # Проверка обязательных директорий
        for directory in [cls.UPLOAD_FOLDER, cls.BACKUP_FOLDER, os.path.dirname(cls.LOG_FILE)]:
            Path(directory).mkdir(parents=True, exist_ok=True)
        
        # Проверка настроек безопасности
        if len(cls.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY должен быть не менее 32 символов")
        
        if len(cls.PASSWORD_SALT) < 16:
            raise ValueError("PASSWORD_SALT должен быть не менее 16 символов")
        
        # Проверка настроек базы данных
        if not cls.SQLALCHEMY_DATABASE_URI:
            raise ValueError("Не указан URI базы данных")
        
        # Проверка настроек Redis
        if not cls.REDIS_URL:
            raise ValueError("Не указан URL Redis")
        
        # Проверка настроек загрузки файлов
        if cls.MAX_CONTENT_LENGTH > 100 * 1024 * 1024:  # 100MB
            raise ValueError("MAX_CONTENT_LENGTH не может быть больше 100MB")
        
        if cls.MAX_FILES_PER_POST > 10:
            raise ValueError("MAX_FILES_PER_POST не может быть больше 10")
        
        # Проверка настроек кэширования
        if cls.CACHE_DEFAULT_TIMEOUT < 60:
            raise ValueError("CACHE_DEFAULT_TIMEOUT не может быть меньше 60 секунд")
        
        # Проверка настроек логирования
        if cls.LOG_MAX_BYTES < 1024 * 1024:  # 1MB
            raise ValueError("LOG_MAX_BYTES не может быть меньше 1MB")
        
        if cls.LOG_BACKUP_COUNT < 1:
            raise ValueError("LOG_BACKUP_COUNT не может быть меньше 1")
        
        # Проверка настроек резервного копирования
        if cls.BACKUP_RETENTION_DAYS < 1:
            raise ValueError("BACKUP_RETENTION_DAYS не может быть меньше 1")
        
        # Проверка настроек модерации
        if cls.MODERATION_QUEUE_SIZE < 10:
            raise ValueError("MODERATION_QUEUE_SIZE не может быть меньше 10")
        
        if cls.MODERATION_TIMEOUT < 300:  # 5 минут
            raise ValueError("MODERATION_TIMEOUT не может быть меньше 5 минут")
        
        # Проверка настроек поиска
        if cls.SEARCH_BATCH_SIZE < 100:
            raise ValueError("SEARCH_BATCH_SIZE не может быть меньше 100")
        
        if cls.SEARCH_MAX_RESULTS < 10:
            raise ValueError("SEARCH_MAX_RESULTS не может быть меньше 10")
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Получение конфигурации в виде словаря."""
        return {
            key: value for key, value in cls.__dict__.items()
            if not key.startswith('_') and not callable(value)
        }
    
    @classmethod
    def get_secret(cls, key: str, default: Optional[str] = None) -> str:
        """Безопасное получение секретного значения."""
        value = os.getenv(key, default)
        if value is None:
            raise ValueError(f"Не найдено значение для {key}")
        return value


class DevelopmentConfig(Config):
    """Конфигурация для разработки."""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    LOG_LEVEL = 'DEBUG'


class TestingConfig(Config):
    """Конфигурация для тестирования."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Конфигурация для продакшена."""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    LOG_LEVEL = 'WARNING'


# Словарь конфигураций
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# Получение текущей конфигурации
current_config = config[os.getenv('FLASK_ENV', 'default')]

# Валидация настроек
current_config.validate() 