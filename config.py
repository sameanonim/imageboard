import os
import secrets
from dotenv import load_dotenv
from datetime import timedelta
from typing import Dict, Any, Optional, Type, List
from pathlib import Path
from dataclasses import dataclass, field
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis

load_dotenv()


@dataclass
class BaseConfig:
    """Базовый класс конфигурации."""

    # Базовые настройки
    SECRET_KEY: str = field(default_factory=lambda: os.getenv('SECRET_KEY', secrets.token_hex(32)))
    DEBUG: bool = field(default_factory=lambda: os.getenv('FLASK_DEBUG', 'False').lower() == 'true')
    TESTING: bool = field(default_factory=lambda: os.getenv('FLASK_TESTING', 'False').lower() == 'true')

    # Локализация
    LANGUAGES: Dict[str, str] = field(default_factory=lambda: {'ru': 'Русский', 'en': 'English'})
    DEFAULT_LANGUAGE: str = field(default_factory=lambda: os.getenv('DEFAULT_LANGUAGE', 'ru'))
    BABEL_DEFAULT_LOCALE: str = field(default_factory=lambda: os.getenv('BABEL_DEFAULT_LOCALE', 'ru'))
    BABEL_DEFAULT_TIMEZONE: str = 'UTC'

    # База данных
    SQLALCHEMY_DATABASE_URI: str = field(default_factory=lambda: os.getenv('DATABASE_URL', 'postgresql://imageboard:imageboard@localhost/imageboard'))
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ENGINE_OPTIONS: Dict[str, int] = field(default_factory=lambda: {
        'pool_size': int(os.getenv('DB_POOL_SIZE', 10)),
        'pool_timeout': int(os.getenv('DB_POOL_TIMEOUT', 30)),
        'pool_recycle': int(os.getenv('DB_POOL_RECYCLE', 3600)),
        'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', 5))
    })

    # Redis
    REDIS_URL: str = field(default_factory=lambda: os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
    REDIS_OPTIONS: Dict[str, Any] = field(default_factory=lambda: {
        'socket_timeout': int(os.getenv('REDIS_TIMEOUT', 5)),
        'socket_connect_timeout': int(os.getenv('REDIS_CONNECT_TIMEOUT', 5)),
        'retry_on_timeout': True,
        'max_connections': int(os.getenv('REDIS_MAX_CONNECTIONS', 10))
    })

    # Celery
    CELERY_BROKER_URL: str = field(default_factory=lambda: os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'))
    CELERY_RESULT_BACKEND: str = field(default_factory=lambda: os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'))
    CELERY_TASK_SERIALIZER: str = 'json'
    CELERY_RESULT_SERIALIZER: str = 'json'
    CELERY_ACCEPT_CONTENT: list = field(default_factory=lambda: ['json'])
    CELERY_TIMEZONE: str = 'UTC'
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_TIME_LIMIT: int = field(default_factory=lambda: int(os.getenv('CELERY_TASK_TIME_LIMIT', 3600)))
    CELERY_TASK_SOFT_TIME_LIMIT: int = field(default_factory=lambda: int(os.getenv('CELERY_TASK_SOFT_TIME_LIMIT', 3000)))

    # Загрузка файлов
    UPLOAD_FOLDER: str = field(default_factory=lambda: os.getenv('UPLOAD_FOLDER', 'uploads'))
    MAX_CONTENT_LENGTH: int = field(default_factory=lambda: int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)))
    ALLOWED_EXTENSIONS: set = field(default_factory=lambda: {'png', 'jpg', 'jpeg', 'gif', 'webp', 'mp4', 'webm'})
    MAX_FILES_PER_POST: int = field(default_factory=lambda: int(os.getenv('MAX_FILES_PER_POST', 4)))
    MAX_IMAGE_SIZE: int = field(default_factory=lambda: int(os.getenv('MAX_IMAGE_SIZE', 4096)))
    THUMBNAIL_SIZE: tuple = (200, 200)
    PREVIEW_SIZE: tuple = (800, 800)

    # Сессии и безопасность
    SESSION_COOKIE_SECURE: bool = field(default_factory=lambda: os.getenv('SESSION_COOKIE_SECURE', 'True').lower() == 'true')
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = 'Lax'
    PERMANENT_SESSION_LIFETIME: timedelta = field(default_factory=lambda: timedelta(days=int(os.getenv('SESSION_LIFETIME_DAYS', 7))))
    REMEMBER_COOKIE_DURATION: timedelta = field(default_factory=lambda: timedelta(days=int(os.getenv('REMEMBER_COOKIE_DAYS', 30))))
    REMEMBER_COOKIE_SECURE: bool = field(default_factory=lambda: os.getenv('SESSION_COOKIE_SECURE', 'True').lower() == 'true')
    REMEMBER_COOKIE_HTTPONLY: bool = True
    REMEMBER_COOKIE_SAMESITE: str = 'Lax'

    # Пароли
    PASSWORD_SALT: str = field(default_factory=lambda: os.getenv('PASSWORD_SALT', secrets.token_hex(16)))
    PASSWORD_MIN_LENGTH: int = field(default_factory=lambda: int(os.getenv('PASSWORD_MIN_LENGTH', 8)))
    PASSWORD_REQUIRE_UPPER: bool = True
    PASSWORD_REQUIRE_LOWER: bool = True
    PASSWORD_REQUIRE_DIGITS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True

    # API
    API_RATE_LIMIT: str = field(default_factory=lambda: os.getenv('API_RATE_LIMIT', '100/hour'))
    API_RATE_LIMIT_STORAGE_URL: str = field(default_factory=lambda: os.getenv('API_RATE_LIMIT_STORAGE_URL', 'redis://localhost:6379/0'))

    # WebSocket
    SOCKET_PING_INTERVAL: int = field(default_factory=lambda: int(os.getenv('SOCKET_PING_INTERVAL', 10)))
    SOCKET_PING_TIMEOUT: int = field(default_factory=lambda: int(os.getenv('SOCKET_PING_TIMEOUT', 20)))
    SOCKET_MAX_CONNECTIONS: int = field(default_factory=lambda: int(os.getenv('SOCKET_MAX_CONNECTIONS', 1000)))
    SOCKETIO_MESSAGE_QUEUE: str = field(default_factory=lambda: os.getenv('SOCKETIO_MESSAGE_QUEUE', 'redis://localhost:6379/0'))
    SOCKETIO_ASYNC_MODE: str = field(default_factory=lambda: os.getenv('SOCKETIO_ASYNC_MODE', 'eventlet'))
    SOCKETIO_PING_TIMEOUT: int = field(default_factory=lambda: int(os.getenv('SOCKETIO_PING_TIMEOUT', 20)))
    SOCKETIO_PING_INTERVAL: int = field(default_factory=lambda: int(os.getenv('SOCKETIO_PING_INTERVAL', 10)))
    SOCKETIO_MAX_HTTP_BUFFER_SIZE: int = field(default_factory=lambda: int(os.getenv('SOCKETIO_MAX_HTTP_BUFFER_SIZE', 1000000)))

    # Кэш
    CACHE_TYPE: str = 'redis'
    CACHE_REDIS_URL: str = field(default_factory=lambda: os.getenv('CACHE_REDIS_URL', 'redis://localhost:6379/0'))
    CACHE_DEFAULT_TIMEOUT: int = field(default_factory=lambda: int(os.getenv('CACHE_TIMEOUT', 300)))
    CACHE_KEY_PREFIX: str = 'imageboard:'
    POPULAR_THREADS_CACHE_KEY: str = 'popular_threads'
    THREAD_CACHE_KEY: str = 'thread_{id}'
    POST_CACHE_KEY: str = 'post_{id}'
    USER_CACHE_KEY: str = 'user_{id}'

    # Логирование
    LOG_FILE: str = field(default_factory=lambda: os.getenv('LOG_FILE', 'logs/imageboard.log'))
    LOG_MAX_BYTES: int = field(default_factory=lambda: int(os.getenv('LOG_MAX_BYTES', 10 * 1024 * 1024)))  # 10MB
    LOG_BACKUP_COUNT: int = field(default_factory=lambda: int(os.getenv('LOG_BACKUP_COUNT', 5)))
    LOG_FORMAT: str = field(default_factory=lambda: os.getenv('LOG_FORMAT', '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    LOG_LEVEL: str = field(default_factory=lambda: os.getenv('LOG_LEVEL', 'INFO'))

    # Резервное копирование
    BACKUP_FOLDER: str = field(default_factory=lambda: os.getenv('BACKUP_FOLDER', 'backups'))
    BACKUP_RETENTION_DAYS: int = field(default_factory=lambda: int(os.getenv('BACKUP_RETENTION_DAYS', 30)))
    BACKUP_SCHEDULE: str = field(default_factory=lambda: os.getenv('BACKUP_SCHEDULE', '0 0 * * *'))

    # Модерация
    MODERATION_QUEUE_SIZE: int = field(default_factory=lambda: int(os.getenv('MODERATION_QUEUE_SIZE', 100)))
    MODERATION_TIMEOUT: int = field(default_factory=lambda: int(os.getenv('MODERATION_TIMEOUT', 3600)))
    MODERATION_NOTIFY_ADMINS: bool = field(default_factory=lambda: os.getenv('MODERATION_NOTIFY_ADMINS', 'True').lower() == 'true')

    # Достижения
    ACHIEVEMENTS_ENABLED: bool = field(default_factory=lambda: os.getenv('ACHIEVEMENTS_ENABLED', 'True').lower() == 'true')
    ACHIEVEMENT_NOTIFICATION_DURATION: int = field(default_factory=lambda: int(os.getenv('ACHIEVEMENT_NOTIFICATION_DURATION', 5000)))

    # Поиск
    SEARCH_INDEX_PATH: str = field(default_factory=lambda: os.getenv('SEARCH_INDEX_PATH', 'search_index'))
    SEARCH_BATCH_SIZE: int = field(default_factory=lambda: int(os.getenv('SEARCH_BATCH_SIZE', 1000)))
    SEARCH_MAX_RESULTS: int = field(default_factory=lambda: int(os.getenv('SEARCH_MAX_RESULTS', 100)))

    # Темы
    THEME_DEFAULT: str = field(default_factory=lambda: os.getenv('THEME_DEFAULT', 'light'))
    THEME_COOKIE_NAME: str = 'theme'
    THEME_COOKIE_DURATION: timedelta = timedelta(days=365)

    # Безопасность
    SECURITY_PASSWORD_SALT: str = field(default_factory=lambda: os.getenv('SECURITY_PASSWORD_SALT', secrets.token_hex(16)))
    SECURITY_PASSWORD_HASH: str = 'bcrypt'
    SECURITY_PASSWORD_LENGTH_MIN: int = 8
    SECURITY_PASSWORD_LENGTH_MAX: int = 128
    SECURITY_PASSWORD_COMPLEXITY: Dict[str, bool] = field(default_factory=lambda: {
        'UPPER': True,
        'LOWER': True,
        'DIGITS': True,
        'SPECIAL': True
    })
    SECURITY_PASSWORD_HISTORY: int = 5
    SECURITY_LOGIN_ATTEMPTS: int = 5
    SECURITY_LOGIN_TIMEOUT: int = 300
    SECURITY_EMAIL_VALIDATOR_ARGS: Dict[str, Any] = field(default_factory=lambda: {
        'check_deliverability': True,
        'test_environment': False
    })
    
    # CSRF защита
    WTF_CSRF_ENABLED: bool = True
    WTF_CSRF_TIME_LIMIT: int = 3600
    WTF_CSRF_SSL_STRICT: bool = True
    
    # CORS
    CORS_ORIGINS: List[str] = field(default_factory=lambda: os.getenv('CORS_ORIGINS', '*').split(','))
    CORS_METHODS: List[str] = field(default_factory=lambda: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    CORS_ALLOW_HEADERS: List[str] = field(default_factory=lambda: ['Content-Type', 'Authorization'])
    CORS_EXPOSE_HEADERS: List[str] = field(default_factory=lambda: ['Content-Range', 'X-Content-Range'])
    CORS_SUPPORTS_CREDENTIALS: bool = True
    
    # XSS защита
    SECURITY_HEADERS: Dict[str, str] = field(default_factory=lambda: {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';"
    })

    # Настройки Redis для rate limiting
    RATELIMIT_STORAGE_URL: str = field(default_factory=lambda: os.getenv('RATELIMIT_STORAGE_URL', 'redis://localhost:6380/1'))
    RATELIMIT_STRATEGY: str = field(default_factory=lambda: os.getenv('RATELIMIT_STRATEGY', 'fixed-window'))
    RATELIMIT_DEFAULT: str = field(default_factory=lambda: os.getenv('RATELIMIT_DEFAULT', '200 per day;50 per hour;10 per minute'))
    RATELIMIT_HEADERS_ENABLED: bool = field(default_factory=lambda: os.getenv('RATELIMIT_HEADERS_ENABLED', 'True').lower() == 'true')

    def validate(self) -> None:
        """Проверка корректности настроек."""
        for directory in [self.UPLOAD_FOLDER, self.BACKUP_FOLDER, os.path.dirname(self.LOG_FILE)]:
            Path(directory).mkdir(parents=True, exist_ok=True)

        if len(self.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY должен быть не менее 32 символов")

        if len(self.PASSWORD_SALT) < 16:
            raise ValueError("PASSWORD_SALT должен быть не менее 16 символов")

        if not self.SQLALCHEMY_DATABASE_URI:
            raise ValueError("Не указан URI базы данных")

        if not self.REDIS_URL:
            raise ValueError("Не указан URL Redis")

        if self.MAX_CONTENT_LENGTH > 100 * 1024 * 1024:
            raise ValueError("MAX_CONTENT_LENGTH не может быть больше 100MB")

        if self.MAX_FILES_PER_POST > 10:
            raise ValueError("MAX_FILES_PER_POST не может быть больше 10")

        if self.CACHE_DEFAULT_TIMEOUT < 60:
            raise ValueError("CACHE_DEFAULT_TIMEOUT не может быть меньше 60 секунд")

        if self.LOG_MAX_BYTES < 1024 * 1024:
            raise ValueError("LOG_MAX_BYTES не может быть меньше 1MB")

        if self.LOG_BACKUP_COUNT < 1:
            raise ValueError("LOG_BACKUP_COUNT не может быть меньше 1")

        if self.BACKUP_RETENTION_DAYS < 1:
            raise ValueError("BACKUP_RETENTION_DAYS не может быть меньше 1")

        if self.MODERATION_QUEUE_SIZE < 10:
            raise ValueError("MODERATION_QUEUE_SIZE не может быть меньше 10")

        if self.MODERATION_TIMEOUT < 300:
            raise ValueError("MODERATION_TIMEOUT не может быть меньше 5 минут")

        if self.SEARCH_BATCH_SIZE < 100:
            raise ValueError("SEARCH_BATCH_SIZE не может быть меньше 100")

        if self.SEARCH_MAX_RESULTS < 10:
            raise ValueError("SEARCH_MAX_RESULTS не может быть меньше 10")

    def get_config(self) -> Dict[str, Any]:
        return {
            key: value for key, value in self.__dict__.items()
            if not key.startswith('_') and not callable(value)
        }

    def get_secret(self, key: str, default: Optional[str] = None) -> str:
        value = os.getenv(key, default)
        if value is None:
            raise ValueError(f"Не найдено значение для {key}")
        return value


@dataclass
class DevelopmentConfig(BaseConfig):
    DEBUG: bool = True
    SQLALCHEMY_ECHO: bool = True
    LOG_LEVEL: str = 'DEBUG'


@dataclass
class TestingConfig(BaseConfig):
    TESTING: bool = True
    SQLALCHEMY_DATABASE_URI: str = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED: bool = False
    LOG_LEVEL: str = 'DEBUG'


@dataclass
class ProductionConfig(BaseConfig):
    DEBUG: bool = False
    TESTING: bool = False
    SESSION_COOKIE_SECURE: bool = True
    REMEMBER_COOKIE_SECURE: bool = True
    LOG_LEVEL: str = 'WARNING'


# Определяем и инициализируем конфигурацию в зависимости от FLASK_ENV
_config_map: Dict[str, Type[BaseConfig]] = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}

# Экспортируем конфигурацию в зависимости от окружения
Config = _config_map[os.getenv('FLASK_ENV', 'development')]()

# Инициализация Redis
redis_client = redis.Redis(
    host='redis',
    port=6379,
    db=1,
    decode_responses=True
)

# Инициализация Limiter
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=Config.RATELIMIT_STORAGE_URL,
    strategy=Config.RATELIMIT_STRATEGY,
    default_limits=[Config.RATELIMIT_DEFAULT],
    headers_enabled=Config.RATELIMIT_HEADERS_ENABLED
)