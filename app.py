from typing import Optional, Callable, Any, Dict, Type
from flask import Flask, request, render_template, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_babel import Babel
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from config import BaseConfig, current_config
from models import db, User
from filters import init_app as init_filters
from celery_config import make_celery
from utils.socket import init_socketio
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
from functools import wraps

# Инициализация расширений
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
babel = Babel()
limiter = Limiter(key_func=get_remote_address)
celery = None
cache = Cache()

def setup_logging(app: Flask) -> None:
    """
    Настройка логирования для приложения.
    
    Args:
        app: Flask приложение
    """
    if not app.debug and not app.testing:
        log_dir = Path(app.config['LOG_FILE']).parent
        log_dir.mkdir(exist_ok=True)
        
        file_handler = RotatingFileHandler(
            app.config['LOG_FILE'],
            maxBytes=app.config['LOG_MAX_BYTES'],
            backupCount=app.config['LOG_BACKUP_COUNT']
        )
        file_handler.setFormatter(logging.Formatter(app.config['LOG_FORMAT']))
        file_handler.setLevel(app.config['LOG_LEVEL'])
        app.logger.addHandler(file_handler)
        app.logger.setLevel(app.config['LOG_LEVEL'])
        app.logger.info('Imageboard startup')

def register_blueprints(app: Flask) -> None:
    """
    Регистрация всех blueprints приложения.
    
    Args:
        app: Flask приложение
    """
    from views.main import main as main_blueprint
    from views.auth import auth as auth_blueprint
    from views.admin import admin as admin_blueprint
    from views.api import api as api_blueprint
    from views.moderation import bp as moderation_blueprint
    
    blueprints = {
        'main': main_blueprint,
        'auth': (auth_blueprint, '/auth'),
        'admin': (admin_blueprint, '/admin'),
        'api': (api_blueprint, '/api'),
        'moderation': (moderation_blueprint, '/mod')
    }
    
    for name, blueprint in blueprints.items():
        if isinstance(blueprint, tuple):
            app.register_blueprint(blueprint[0], url_prefix=blueprint[1])
        else:
            app.register_blueprint(blueprint)
        app.logger.info(f'Registered blueprint: {name}')

def register_error_handlers(app: Flask) -> None:
    """
    Регистрация обработчиков ошибок.
    
    Args:
        app: Flask приложение
    """
    @app.errorhandler(404)
    def not_found_error(error: Any) -> tuple[str, int]:
        app.logger.warning(f'Page not found: {request.url}')
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error: Any) -> tuple[str, int]:
        db.session.rollback()
        app.logger.error(f'Server Error: {error}')
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error: Any) -> tuple[str, int]:
        app.logger.warning(f'Forbidden: {request.url}')
        return render_template('errors/403.html'), 403

def init_extensions(app: Flask) -> None:
    """
    Инициализация расширений Flask.
    
    Args:
        app: Flask приложение
    """
    # Инициализация базы данных
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Инициализация аутентификации
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'
    login_manager.login_message_category = 'info'
    
    # Инициализация локализации
    babel.init_app(app, locale_selector=lambda: session.get('lang', app.config['DEFAULT_LANGUAGE']))
    
    # Инициализация ограничителя запросов
    limiter.init_app(app)
    limiter.storage_uri = app.config['REDIS_URL']
    
    # Инициализация кэширования
    cache.init_app(app)
    
    # Инициализация Celery
    global celery
    celery = make_celery(app)
    
    # Инициализация SocketIO
    init_socketio(app)
    
    app.logger.info('Initialized all extensions')

def create_app(config_class: Type[BaseConfig] = current_config.__class__) -> Flask:
    """
    Создание и настройка приложения Flask.
    
    Args:
        config_class: Класс конфигурации приложения
        
    Returns:
        Flask: Настроенное приложение Flask
    """
    app = Flask(__name__)
    app.config.update(config_class().get_config())
    
    # Настройка логирования
    setup_logging(app)
    
    # Инициализация расширений
    init_extensions(app)
    
    # Обработка языка
    @app.before_request
    def before_request() -> None:
        """Обработка запроса перед его выполнением."""
        if request.args.get('lang'):
            session['lang'] = request.args.get('lang')
    
    # Регистрация blueprints
    register_blueprints(app)
    
    # Регистрация фильтров
    init_filters(app)
    
    # Регистрация обработчиков ошибок
    register_error_handlers(app)
    
    # Инициализация базы данных
    with app.app_context():
        db.create_all()
    
    # Регистрация CLI команд
    from cli import init_app as init_cli
    init_cli(app)
    
    app.logger.info('Application created successfully')
    return app

@login_manager.user_loader
def load_user(id: str) -> Optional[User]:
    """
    Загрузка пользователя для Flask-Login.
    
    Args:
        id: ID пользователя
        
    Returns:
        Optional[User]: Объект пользователя или None
    """
    return User.query.get(int(id))

def with_app_context(f: Callable) -> Callable:
    """
    Декоратор для выполнения функции в контексте приложения.
    
    Args:
        f: Функция для выполнения
        
    Returns:
        Callable: Обернутая функция
    """
    @wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        with app.app_context():
            return f(*args, **kwargs)
    return wrapper

app = create_app()

if __name__ == '__main__':
    app.run(
        host=os.getenv('FLASK_HOST', '127.0.0.1'),
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=app.config['DEBUG']
    ) 